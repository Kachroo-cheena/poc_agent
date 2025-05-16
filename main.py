import re, os, base64
import asyncio
import streamlit as st
from openai import OpenAI
from dotenv import load_dotenv
import boto3
from urllib.parse import urlparse

load_dotenv(override=True)
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
from playwright.async_api import async_playwright, TimeoutError as PlaywrightTimeoutError

# --- Configuration ---
URL = "https://byron-council.maps.arcgis.com/apps/instant/sidebar/index.html?appid=c741bd7f05e2485fb288bd45cc1a2c5c"
  # set in Streamlit secrets
aws_access_key = os.getenv("AWS_ACCESS_KEY_ID")
aws_secret_key = os.getenv("AWS_SECRET_ACCESS_KEY")
aws_region = os.getenv("AWS_REGION")
s3_bucket = os.getenv("BUCKET_NAME")
session = boto3.Session(
        aws_access_key_id=aws_access_key,
        aws_secret_access_key=aws_secret_key,
        region_name=aws_region,
    )
s3_client = session.client("s3")

# --- AWS S3 Upload Helper ---
def upload_to_s3(file_path: str, bucket: str, object_name: str) -> str:
    """Uploads file to S3 and returns the S3 object URL."""
    s3_client.upload_file(file_path, bucket, object_name,ExtraArgs={'ACL': 'public-read'})
    # Construct object URL (region-specific)
    return f"https://{bucket}.s3.{aws_region}.amazonaws.com/{object_name}"

def get_presigned_url(bucket: str, object_name: str, expires_in: int = 3600) -> str:
    """Generates a presigned URL for the given S3 object."""
    return s3_client.generate_presigned_url(
        ClientMethod='get_object',
        Params={'Bucket': bucket, 'Key': object_name},
        ExpiresIn=expires_in
    )

# --- Playwright steps ---
def tokenize_address(addr: str):
    return re.findall(r'[^ ,\-]+|[ ,\-]', addr)

async def close_disclaimer(page):
    try:
        await page.click("button[aria-label='Close']", timeout=5000)
    except PlaywrightTimeoutError:
        pass

async def search_and_select(page, address: str):
    INPUT = 'input[aria-label="Search for an address"], input[placeholder="Search for an address"]'
    await page.wait_for_selector(INPUT, timeout=10000)
    search = page.locator(INPUT)

    for tok in tokenize_address(address):
        curr = await search.input_value()
        await search.fill(curr + tok)
        await page.wait_for_timeout(2000)
        count = await page.locator(".esri-search__form div.interaction-container").count()
        if count == 3:
            # pick second (first suggestion)
            await page.locator(".esri-search__form div.interaction-container >> nth=1").click()
            break

    # fallback: press enter
    await page.keyboard.press("Enter")
    await page.wait_for_timeout(1500)

async def expand_layers(page):
    await page.click('button[aria-label="Layers"]')
    await page.wait_for_timeout(500)
    FLOOD_INFO = "div[aria-label='Flood Information '] >> nth=0"
    locator = page.locator(FLOOD_INFO)
    await locator.click()
    await locator.locator("div.open-container").click()
    layers = [
        'Flood model catchments',
        'Fill Exclusion Zones',
        'Floor Level Survey 2016 2019',
        'Flood Planning Area (West Byron)',
        'Flood Planning Area (Areas Affected by Flood - refer to Byron Shire Development Control Plan  2014 Chapter C2)',
        'Flood Prone (Liable) Lands (land susceptible to flooding by the PMF event Refer to Byron Shire Development Control Plan 2010 Chapter 1: Part K)',
        'North Byron 2020 100yr 2100 CC Hazard',
        'North Byron 2020 Existing Climate Hazard',
        'Belongil 2015 Flood Hazard Layers'
    ]
    for name in layers:
        selector = f"div[aria-label='{name}']  >> nth=0"
        try:
            await page.click(selector)
            await page.wait_for_timeout(300)
        except PlaywrightTimeoutError:
            pass

async def run_automation(address: str, screenshot_path: str = "flood_zone.png") -> str:
    async with async_playwright() as pw:
        browser = await pw.chromium.launch(headless=False)
        page = await browser.new_page()
        await page.goto(URL, timeout=60000)
        await asyncio.sleep(10)
        await close_disclaimer(page)
        await search_and_select(page, address)
        await page.wait_for_timeout(3000)
        await expand_layers(page)
        # zoom a few times for clarity
        for _ in range(7):
            await page.click("button[aria-label='Zoom in']")
            await page.wait_for_timeout(200)
        # final pause then screenshot
        await page.wait_for_timeout(20000)
        await page.screenshot(path=screenshot_path)
        await browser.close()
    return screenshot_path

# --- OpenAI image summary ---
def generate_summary(s3_url: str) -> str:
    # send image + prompt to OpenAI Vision-enabled model
    # with open(image_path, "rb") as img:
    # b64 = base64.b64encode(open(image_path, "rb").read()).decode()
    # file = client.files.create( file=open(image_path, "rb"), purpose="fine-tune" ) 

    prompt = (
        f"Please generate a comprehensive, self-contained flood risk report for the property shown in the\n Your summary should include:\n - A clear statement on whether the property lies within any identified flood zones.\n- Specific details on which areas of the property (e.g., front boundary, driveway, central lot, backyard) are affected.\n- The types of flood hazards or scenarios depicted (e.g., existing climate hazard, 100-year future flood, local flood hazard layer).\n- Any notable severity or depth indications visible on the map.\n- A concise conclusion that allows a reader to fully understand the property’s flood exposure without viewing the map." 
    )
    response = client.chat.completions.create(model="gpt-4o",
    messages=[
        {"role": "user", "content": [
          
          {
            "type": "image_url",
            "image_url": {
              "url":  s3_url, 
            },
            
          },
          { "type": "text", "text": prompt }
        ]
               
               }])
    return response.choices[0].message.content.strip()

# --- Streamlit UI ---
def main():
    st.title("Flood Zone Analyzer")
    address = st.text_input("Enter property address:", "148-154 Jonson Street, Byron Bay NSW 2481")
    if st.button("Analyze Flood Risk"):
        with st.spinner("Running map automation..."):
            try:
                screenshot_path = asyncio.run(run_automation(address))
            except Exception as e:
                st.error(f"Automation error: {e}")
                return
        key = f"flood_maps/{address.replace(' ', '_').replace(',', '')}.png"
        try:
            object_url = upload_to_s3(screenshot_path, s3_bucket, key)
            st.markdown(f"**S3 Object URL:** {object_url}")
        except Exception as e:
            st.error(f"S3 upload error: {e}")
            return

        # 2) Derive key from URL and generate presigned URL
        parsed = urlparse(object_url)
        object_name = parsed.path.lstrip('/')
        try:
            presigned_url = get_presigned_url(s3_bucket, object_name)
            st.markdown(f"**Presigned URL (1hr expiry):** [View map]({presigned_url})")
        except Exception as e:
            st.error(f"Presign URL error: {e}")
            return
        st.image(screenshot_path, caption="Flood Zone Map", use_column_width=True)
        # screenshot_path = "flood_zone.png"
        with st.spinner("Generating summary..."):
            try:
                summary = generate_summary(presigned_url)
            except Exception as e:
                st.error(f"OpenAI error: {e}")
                return
        st.markdown("**Flood Risk Summary:**")
        st.write(summary)

if __name__ == "__main__":
    main()
