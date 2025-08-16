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


# --- NEW: Generative features (cover letter, interview Qs, skill gap + learning path) ---
def generate_cover_letter(resume_text, job_description=None):
    """Generate a tailored cover letter using Gemini."""
    model = genai.GenerativeModel("gemini-1.5-flash")
    prompt = f"""
    You are an expert HR professional and professional writer. 
    Create a concise, persuasive cover letter (about 3-5 short paragraphs, ~200-300 words) tailored to the candidate described in the resume below.
    Make the tone professional and impactful, emphasizing key achievements and fit for the role.
    
    Resume:
    {resume_text}
    """
    if job_description:
        prompt += f"\nTarget Job Description:\n{job_description}\nPlease tailor the letter specifically to the job description."
    # Ask for a short sign-off
    prompt += "\nEnd with a short, professional closing and a call to action."

    response = model.generate_content(prompt)
    return response.text.strip()


def generate_interview_questions(resume_text, job_description=None, count=8):
    """Generate role-specific interview questions based on resume and optional job description."""
    model = genai.GenerativeModel("gemini-1.5-flash")
    prompt = f"""
    You are an experienced hiring manager and interviewer.
    Based on the resume below, generate {count} interview prompts/questions that assess:
    - technical skills and knowledge,
    - problem-solving / work examples,
    - behavioural fit.
    Provide questions as a numbered list. Keep them focused and role-relevant.
    
    Resume:
    {resume_text}
    """
    if job_description:
        prompt += f"\nJob Description:\n{job_description}\nPrioritize questions relevant to this job."

    response = model.generate_content(prompt)
    return response.text.strip()


def generate_skill_gap_learning_path(resume_text, job_description=None, top_n_courses=3):
    """Identify skill gaps and propose a concise learning path with recommended resources."""
    model = genai.GenerativeModel("gemini-1.5-flash")
    prompt = f"""
    You are a career coach and technical instructor.
    1) Identify up to 5 key skill gaps relative to the resume (and to the job description if provided).
    2) For each gap, give a 1-2 sentence explanation why it matters.
    3) For each gap, recommend a short, actionable learning path (3 steps max) and up to {top_n_courses} recommended courses or resources (name + platform).
    
    Output clearly with headings: Skill Gap, Why it matters, Learning Path, Recommended Resources.
    
    Resume:
    {resume_text}
    """
    if job_description:
        prompt += f"\nJob Description:\n{job_description}\nFocus recommendations toward this job."

    response = model.generate_content(prompt)
    return response.text.strip()
# --- END NEW FUNCTIONS ---


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
                analysis = analyze_resume(resume_text, job_description if job_description.strip() else None)
                st.success("✅ Analysis complete!")
    
                import re
    
                # --- ATS Score ---
                ats_match = re.search(r"ATS Score:\s*(\d+)", analysis)
                ats_score = int(ats_match.group(1)) if ats_match else 0
                st.markdown("### 📊 ATS Score")
                st.progress(ats_score / 100)
                color = "green" if ats_score >= 80 else "orange" if ats_score >= 60 else "red"
                st.markdown(
                    f"<h2 style='color:{color};text-align:center'>{ats_score}%</h2>",
                    unsafe_allow_html=True
                )
    
                # --- Skills Present ---
                st.markdown("### ✅ Skills Present")
                skills_present = re.findall(
                    r"- (.+)", analysis.split("Skills Present:")[1].split("Skills to Improve")[0]
                )
                st.markdown(
                    " ".join([
                        f"<span style='background-color:#e0f7e9; padding:6px 10px; border-radius:20px; margin:4px; display:inline-block; font-size:14px'>{skill}</span>"
                        for skill in skills_present
                    ]),
                    unsafe_allow_html=True
                )
    
                # --- Skills Missing ---
                st.markdown("### ❌ Skills Missing")
                skills_missing = re.findall(
                    r"- (.+)", analysis.split("Skills to Improve/Add:")[1].split("Recommended Courses")[0]
                )
                st.markdown(
                    " ".join([
                        f"<span style='background-color:#ffe0e0; padding:6px 10px; border-radius:20px; margin:4px; display:inline-block; font-size:14px'>{skill}</span>"
                        for skill in skills_missing
                    ]),
                    unsafe_allow_html=True
                )
    
                # --- Recommended Courses ---
                st.markdown("### 📚 Recommended Courses")
                courses = re.findall(
                    r"- (.+)", analysis.split("Recommended Courses:")[1].split("Strengths")[0]
                )
                for c in courses:
                    st.markdown(f"🎓 {c}")
    
                # --- Strengths & Weaknesses ---
                col1, col2 = st.columns(2)
                with col1:
                    st.markdown("### 💪 Strengths")
                    strengths = re.findall(
                        r"- (.+)", analysis.split("Strengths:")[1].split("Weaknesses")[0]
                    )
                    for s in strengths:
                        st.markdown(
                            f"<div style='background-color:#e8f5e9; padding:6px; border-radius:8px; margin-bottom:4px; font-size:14px'>🟢 {s}</div>",
                            unsafe_allow_html=True
                        )
                with col2:
                    st.markdown("### ⚠️ Weaknesses")
                    weaknesses = re.findall(
                        r"- (.+)", analysis.split("Weaknesses / Areas for Improvement:")[1].split("Overall Fit")[0]
                    )
                    for w in weaknesses:
                        st.markdown(
                            f"<div style='background-color:#ffebee; padding:6px; border-radius:8px; margin-bottom:4px; font-size:14px'>🔴 {w}</div>",
                            unsafe_allow_html=True
                        )
    
                
                st.markdown("### 📌 Overall Fit")
                overall_fit = analysis.split("Overall Fit:")[1].strip()
                st.markdown(
                    f"<div style='background-color:#fff3cd; padding:10px; border-radius:8px; font-style:italic; font-size:14px'>{overall_fit}</div>",
                    unsafe_allow_html=True
                )

               
                has_jd = bool(job_description and job_description.strip())
                if not has_jd:
                    st.info("Enter a job description to enable cover letter, interview questions, and skill-gap recommendations.")

                gen_col1, gen_col2, gen_col3 = st.columns(3)
                with gen_col1:
                    if st.button("Generate Cover Letter", disabled=not has_jd):
                        with st.spinner("Generating cover letter..."):
                            try:
                                cover_letter = generate_cover_letter(resume_text, job_description if has_jd else None)
                                st.markdown("### 📝 Generated Cover Letter")
                                st.text_area("Cover Letter", cover_letter, height=280)
                            except Exception as e:
                                st.error(f"Cover letter generation failed: {e}")
                with gen_col2:
                    if st.button("Generate Interview Questions", disabled=not has_jd):
                        with st.spinner("Generating interview questions..."):
                            try:
                                questions = generate_interview_questions(resume_text, job_description if has_jd else None, count=8)
                                st.markdown("### 🎤 Interview Questions")
                                st.text_area("Interview Questions", questions, height=220)
                            except Exception as e:
                                st.error(f"Interview question generation failed: {e}")
                with gen_col3:
                    if st.button("Generate Skill Gap & Learning Path", disabled=not has_jd):
                        with st.spinner("Analyzing skill gaps and generating learning path..."):
                            try:
                                skill_gap_path = generate_skill_gap_learning_path(resume_text, job_description if has_jd else None, top_n_courses=3)
                                st.markdown("### 📚 Skill Gaps & Learning Path")
                                st.text_area("Skill Gaps & Learning Path", skill_gap_path, height=300)
                            except Exception as e:
                                st.error(f"Skill gap generation failed: {e}")
                # --- end new buttons ---
            except Exception as e:
                st.error(f"Analysis failed: {e}")



#Footer
st.markdown("---")
st.markdown("""<p style= 'text-align: center;' >Powered by <b>Streamlit</b> and <b>Google Gemini AI</b> | Developed by <a href="https://www.linkedin.com/in/dutta-sujoy/"  target="_blank" style='text-decoration: none; color: #FFFFFF'><b>Sujoy Dutta</b></a></p>""", unsafe_allow_html=True)
