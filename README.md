# Resume Analyzer (Streamlit + Google Gemini AI)

This project is a Streamlit-based web application that processes a user’s resume, extracts its contents, and performs an analysis using Google Gemini AI. The system evaluates the resume from the perspective of an ATS (Applicant Tracking System), identifies missing skills, generates interview questions, produces cover letters tailored to job descriptions, and offers a personalized skill-gap learning path. The project is intended as an academic demonstration of how large language models can assist in automated resume evaluation and career guidance.

## Features

### 1. Resume Text Extraction
The application accepts PDF resumes and extracts text using two methods:
- Direct extraction using `pdfplumber`
- OCR extraction via `pytesseract` for image-based or scanned PDFs

### 2. Gemini-Based Resume Analysis
After extracting the text, the system uses Google Gemini (1.5 Flash) to generate:
- ATS score (0–100)
- Skills present in the resume
- Skills missing or recommended for improvement
- Recommended courses
- Strengths and weaknesses
- A brief overall fit summary

### 3. Job Description Matching
Users may optionally provide a job description. When supplied, the analysis, cover letter, interview questions, and skill-gap insights are tailored specifically to that role.

### 4. Generative Career Tools
The application provides additional AI-powered utilities:
- Tailored cover letter generation  
- Interview question generation  
- Skill gap identification and learning path recommendations  

These tools are available once the primary analysis is completed.

### 5. Interactive User Interface
Built with Streamlit, the interface includes:
- PDF uploader  
- Job description text box  
- ATS score visualization  
- Structured sections for skills, strengths, weaknesses, and recommendations  
- Buttons to generate additional AI outputs  
- Persistent state handling using `st.session_state`

## Project Structure

The primary logic is contained in `app.py`, which includes:
- PDF parsing and OCR handling  
- Gemini API configuration  
- Prompt templates for analysis and generation  
- Streamlit UI layout  
- Session state management  

## Requirements

Python Libraries:
- streamlit  
- python-dotenv  
- google-generativeai  
- pdfplumber  
- pdf2image  
- pytesseract  
- Pillow  

System Dependencies:
- Tesseract OCR  
- Poppler (required for `pdf2image`)  

The Google API key must be added inside Streamlit Secrets as:

 st.secrets["Google_API_Key"]

 
## Running the Application

1. Clone the repository.
2. Install required Python libraries.
3. Install Tesseract OCR and Poppler.
4. Add your Google API key to Streamlit Secrets.
5. Run the application:


Once launched, the application will open in the browser, allowing resume upload and analysis.

## Notes

- The project is designed for academic and demonstration purposes.
- The quality of results depends on resume clarity and completeness of job descriptions.
- This system should not be treated as a replacement for professional recruitment tools.

