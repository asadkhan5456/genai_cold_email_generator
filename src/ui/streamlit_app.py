# src/ui/streamlit_app.py
import streamlit as st
import requests
import json

st.set_page_config(layout="wide", page_title="Cold Email Generator", page_icon="📧")
st.title("📧 Cold Email Generator")

st.markdown("### Step 1: Extract Job Details")
job_url = st.text_input("Enter the URL of the company's careers page:", value="https://jobs.nike.com/job/R-55026")

if st.button("Extract Job Data"):
    try:
        response = requests.post("http://api:8080/extract_job", json={"url": job_url})
        response.raise_for_status()
        job_details = response.json().get("job_details", "{}")
        try:
            job_data = json.loads(job_details) if isinstance(job_details, str) else job_details
            st.success("Job data extracted successfully!")
            st.session_state.job_data = job_data
        except Exception as e:
            st.error(f"Error parsing job details: {e}")
    except Exception as e:
        st.error(f"Error extracting job data: {e}")

st.markdown("---")
st.markdown("### Step 2: Generate Cold Email")

if "job_data" in st.session_state:
    job_data = st.session_state.job_data
else:
    job_data = None

if job_data:
    st.markdown("#### Using Extracted Job Details")
    st.write(job_data)
    
    st.markdown("#### Enter Recipient & Customization Details")
    recipient_name = st.text_input("Recipient Name", "Hiring Manager")
    industry = st.text_input("Industry", "Healthcare")
    tone = st.text_input("Tone", "professional and friendly")
    
    st.markdown("#### Enter Portfolio Information")
    techstack = st.text_input("Enter your Tech Stack", "Python, FastAPI, PostgreSQL")
    portfolio_link = st.text_input("Enter your Portfolio Link", "https://example.com/portfolio")
    
    if st.button("Generate Cold Email"):
        payload = {
            "job_data": job_data,
            "techstack": techstack,
            "portfolio_link": portfolio_link,
            "recipient_name": recipient_name,
            "industry": industry,
            "tone": tone
        }
        try:
            response = requests.post("http://api:8080/generate_email", json=payload)
            response.raise_for_status()
            email_content = response.json().get("generated_email", "")
            st.subheader("Generated Cold Email:")
            st.text_area("Email Output", email_content, height=300)
        except Exception as e:
            st.error(f"Error generating email: {e}")
else:
    st.info("Please extract job data first by entering a valid URL and clicking 'Extract Job Data'.")
