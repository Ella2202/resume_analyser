import os
from dotenv import load_dotenv
from PIL import Image
import google.generativeai as genai
from pdf2image import convert_from_path
import pytesseract
import pdfplumber
import streamlit as st

# Load environment variables (GOOGLE_API_KEY must be set in Hugging Face Secrets)
load_dotenv()

# Configure Google Gemini AI

api_key = st.secrets.get("Google_API_Key")
if not api_key:
    raise ValueError("❌ GOOGLE_API_KEY not found in environment variables or Streamlit secrets")

genai.configure(api_key=api_key)



# Function to extract text from PDF
def extract_text_from_pdf(pdf_path):
    text = ""
    try:
        # First try direct text extraction
        with pdfplumber.open(pdf_path) as pdf:
            for page in pdf.pages:
                page_text = page.extract_text()
                if page_text:
                    text += page_text
        if text.strip():
            return text.strip()
    except Exception as e:
        print(f"Direct text extraction failed: {e}")

    # Fallback to OCR for image-based PDFs
    print("Falling back to OCR for image-based PDF.")
    try:
        images = convert_from_path(pdf_path)
        for image in images:
            page_text = pytesseract.image_to_string(image)
            text += page_text + "\n"
    except Exception as e:
        print(f"OCR failed: {e}")

    return text.strip()

# Function to analyze resume using Gemini
def analyze_resume(file, job_description):
    if file is None:
        return "❌ Please upload a PDF resume."

    # Save uploaded file locally
    pdf_path = "uploaded_resume.pdf"
    with open(pdf_path, "wb") as f:
        f.write(file.read())

    # Extract text
    resume_text = extract_text_from_pdf(pdf_path)
    if not resume_text:
        return "⚠ No text found in the uploaded resume."

    model = genai.GenerativeModel("gemini-1.5-flash")

    base_prompt = f"""
    You are an experienced HR with technical expertise in roles such as Data Science, Data Analyst, DevOps, 
    Machine Learning Engineer, Prompt Engineer, AI Engineer, Full Stack Web Developer, Big Data Engineer, 
    Marketing Analyst, Human Resource Manager, or Software Developer.
    Review the provided resume and share your evaluation. 
    Mention:
    1. Skills the candidate already has.
    2. Skills to improve.
    3. Relevant courses to take.
    4. Strengths and weaknesses.

    Resume:
    {resume_text}
    """

    if job_description:
        base_prompt += f"""
        Additionally, compare this resume to the following job description:
        
        Job Description:
        {job_description}

        Highlight strengths and weaknesses of the applicant in relation to the job requirements.
        """

    try:
        response = model.generate_content(base_prompt)
        return response.text.strip()
    except Exception as e:
        return f"❌ Analysis failed: {e}"

# Build Gradio UI
with gr.Blocks() as demo:
    gr.Markdown("# 📄 AI Resume Analyzer")
    gr.Markdown("Upload your resume and (optionally) add a job description for an AI-powered analysis using **Google Gemini AI**.")

    with gr.Row():
        resume_file = gr.File(label="Upload Resume (PDF)", file_types=[".pdf"])
        job_desc = gr.Textbox(label="Job Description (Optional)", placeholder="Paste job description here...", lines=8)

    analyze_btn = gr.Button("Analyze Resume")
    output_text = gr.Textbox(label="AI Analysis", lines=20)

    analyze_btn.click(fn=analyze_resume, inputs=[resume_file, job_desc], outputs=output_text)

    gr.Markdown("---")
    gr.Markdown("Powered by **Gradio** & **Google Gemini AI** | Adapted for Hugging Face Spaces 🚀")

# Run locally (for testing)
if __name__ == "__main__":
    demo.launch()
