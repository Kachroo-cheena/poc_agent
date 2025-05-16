Here’s a `README.md` file tailored for your Streamlit-based **Flood Zone Analyzer** project, including setup instructions, features, and usage steps:

---

```markdown
# 🏠 Flood Zone Analyzer

A Streamlit web application that automates the retrieval and analysis of flood zone information for properties using Byron Council's GIS map tool. It combines browser automation via Playwright, AWS S3 for image storage, and OpenAI's Vision model to generate a descriptive summary of flood exposure from captured screenshots.

---

## 🚀 Features

- 🔎 Automates flood map search and layer expansion using Playwright
- 📸 Takes a screenshot of the flood map for a given property address
- ☁️ Uploads map image to AWS S3 with public-read access
- 🔐 Generates a presigned URL for secure short-term access
- 🧠 Uses OpenAI's GPT-4 Vision model to summarize the flood impact visually
- 🖥️ Easy-to-use interface via Streamlit

---

## 📦 Project Structure

```

.
├── main.py                 # Streamlit app and backend logic
├── .env                   # Environment variables
├── requirements.txt       # Python dependencies
└── README.md              # Project overview

````

---

## 🔧 Setup Instructions

### 1. Clone the Repository

```bash
git clone https://github.com/your-username/flood-zone-analyzer.git
cd flood-zone-analyzer
````

### 2. Install Dependencies

```bash
pip install -r requirements.txt
```

### 3. Environment Variables

Create a `.env` file in the root directory with the following keys:

```env
OPENAI_API_KEY=your_openai_api_key
AWS_ACCESS_KEY_ID=your_aws_access_key
AWS_SECRET_ACCESS_KEY=your_aws_secret_key
AWS_REGION=your_aws_region
BUCKET_NAME=your_s3_bucket_name
```

> ✅ Ensure your S3 bucket is configured to allow `public-read` access if using `upload_to_s3()` directly.

### 4. Run the App

```bash
streamlit run main.py
```

---

## 🖼️ How It Works

1. **User Input:** Enter the property address in the Streamlit UI.
2. **Automation:** The Playwright script opens the Byron Council map tool, searches the address, expands flood information layers, and takes a screenshot.
3. **Upload:** The screenshot is uploaded to AWS S3.
4. **Presigned URL:** A temporary, secure URL is generated for OpenAI to access the image.
5. **Summary:** OpenAI's GPT-4 Vision API analyzes the image and provides a detailed flood risk report.
6. **Display:** The image and summary are shown in the Streamlit app.

---

## 🧠 Prompt Design (OpenAI)

The prompt sent to GPT-4 Vision includes:

* Flood zone presence
* Affected areas (e.g., driveway, backyard)
* Types of flood hazards
* Severity or depth indications
* Human-readable conclusion

---

## ✅ Dependencies

* `playwright`
* `streamlit`
* `openai`
* `boto3`
* `python-dotenv`

Install Playwright dependencies:

```bash
playwright install
```

---

## 🛡️ Disclaimer

This tool uses publicly accessible data from Byron Council's GIS portal. It is intended for informational purposes only and not for legal or property purchase decisions.

---

## 📬 Contact

For issues or improvements, feel free to open an issue or contact [cheenak.ds@gmail.com](mailto:your-email@example.com).

```

---

Let me know if you want the markdown converted to PDF or if you'd like the GitHub `requirements.txt` added too.
```
