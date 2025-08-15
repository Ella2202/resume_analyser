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
def analyze_resume(resume_text, job_description=None):
    if not resume_text:
        return {"error": "Resume text is required for analysis."}
    
    model = genai.GenerativeModel("gemini-1.5-flash")
    
    base_prompt = f"""
    You are a highly experienced HR professional with strong technical expertise in one or more of the following roles:
    Data Scientist, Data Analyst, DevOps Engineer, Machine Learning Engineer, Prompt Engineer, AI Engineer, Full Stack Developer, Big Data Engineer, Marketing Analyst, Human Resource Manager, or Software Developer.
    
    Your task is to review the provided resume as if you are preparing an ATS and recruiter evaluation.
    
    Respond ONLY in the following format — do not add any extra commentary, markdown code blocks, or introductions.
    
    ---
    ATS Score: <score between 0–100>
    
    Skills Present:
    - Skill 1
    - Skill 2
    - Skill 3
    
    Skills to Improve/Add:
    - Missing Skill 1
    - Missing Skill 2
    - Missing Skill 3
    
    Recommended Courses:
    - Course Name (Platform)
    - Course Name (Platform)
    
    Strengths:
    - Strength 1
    - Strength 2
    - Strength 3
    
    Weaknesses / Areas for Improvement:
    - Weakness 1
    - Weakness 2
    - Weakness 3
    
    Overall Fit:
    <2–3 sentence summary of candidate’s suitability for the target role>
    ---
    
    Keep it concise, clear, and actionable.

    Resume:
    {resume_text}
    """

    if job_description:
        base_prompt += f"""
        Additionally, compare this resume to the following job description:
        
        Job Description:
        {job_description}
        
        Highlight the strengths and weaknesses of the applicant in relation to the specified job requirements.
        """

    response = model.generate_content(base_prompt)

    analysis = response.text.strip()
    return analysis


# Streamlit app

st.set_page_config(page_title="Resume Analyzer", layout="wide")
# Title
st.title("AI Resume Analyzer")
st.write("Analyze your resume and match it with job descriptions using Google Gemini AI.")

col1 , col2 = st.columns(2)
with col1:
    uploaded_file = st.file_uploader("Upload your resume (PDF)", type=["pdf"])
with col2:
    job_description = st.text_area("Enter Job Description:", placeholder="Paste the job description here...")

if uploaded_file is not None:
    st.success("Resume uploaded successfully!")
else:
    st.warning("Please upload a resume in PDF format.")


st.markdown("<div style= 'padding-top: 10px;'></div>", unsafe_allow_html=True)
if uploaded_file:
    # Save uploaded file locally for processing
    with open("uploaded_resume.pdf", "wb") as f:
        f.write(uploaded_file.getbuffer())
    # Extract text from PDF
    resume_text = extract_text_from_pdf("uploaded_resume.pdf")

    if st.button("Analyze Resume"):
        with st.spinner("Analyzing resume..."):
            try:
                analysis = analyze_resume(resume_text, job_description)
                st.success("✅ Analysis complete!")
    
                # Parse ATS score
                import re
                ats_match = re.search(r"ATS Score:\s*(\d+)", analysis)
                ats_score = int(ats_match.group(1)) if ats_match else 0
    
                # ATS Score Display
                st.subheader("📊 ATS Score")
                st.progress(ats_score / 100)
                st.markdown(f"<h2 style='color: {'green' if ats_score >= 80 else 'orange' if ats_score >= 60 else 'red'}'>{ats_score}%</h2>", unsafe_allow_html=True)
    
                # Skills Present
                st.subheader("✅ Skills Present")
                skills_present = re.findall(r"- (.+)", analysis.split("Skills Present:")[1].split("Skills to Improve")[0])
                st.markdown(" ".join([f"<span style='background-color:#e0f7e9; padding:4px 8px; border-radius:5px; margin:3px; display:inline-block'>{skill}</span>" for skill in skills_present]), unsafe_allow_html=True)
    
                # Skills Missing
                st.subheader("❌ Skills Missing")
                skills_missing = re.findall(r"- (.+)", analysis.split("Skills to Improve/Add:")[1].split("Recommended Courses")[0])
                st.markdown(" ".join([f"<span style='background-color:#ffe0e0; padding:4px 8px; border-radius:5px; margin:3px; display:inline-block'>{skill}</span>" for skill in skills_missing]), unsafe_allow_html=True)
    
                # Strengths & Weaknesses
                col1, col2 = st.columns(2)
                with col1:
                    st.markdown("**💪 Strengths**")
                    strengths = re.findall(r"- (.+)", analysis.split("Strengths:")[1].split("Weaknesses")[0])
                    for s in strengths:
                        st.markdown(f"✅ {s}")
                with col2:
                    st.markdown("**⚠️ Weaknesses**")
                    weaknesses = re.findall(r"- (.+)", analysis.split("Weaknesses / Areas for Improvement:")[1].split("Overall Fit")[0])
                    for w in weaknesses:
                        st.markdown(f"❌ {w}")
    
                # Overall Fit
                st.subheader("📌 Overall Fit")
                overall_fit = analysis.split("Overall Fit:")[1].strip()
                st.info(overall_fit)
    
            except Exception as e:
                st.error(f"Analysis failed: {e}")


#Footer
st.markdown("---")
st.markdown("""<p style= 'text-align: center;' >Powered by <b>Streamlit</b> and <b>Google Gemini AI</b> | Developed by <a href="https://www.linkedin.com/in/dutta-sujoy/"  target="_blank" style='text-decoration: none; color: #FFFFFF'><b>Sujoy Dutta</b></a></p>""", unsafe_allow_html=True)
