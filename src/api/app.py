# src/api/app.py
import sys
import os
os.environ["USER_AGENT"] = "Mozilla/5.0 (compatible; GenAIColdEmailBot/1.0; +http://yourdomain.com)"

project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if project_root not in sys.path:
    sys.path.append(project_root)

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import os
import re
import uuid
import chromadb
import pandas as pd
from langchain_community.document_loaders import WebBaseLoader
from api.chains import Chain
from dotenv import load_dotenv

load_dotenv()

app = FastAPI(title="GenAI Cold Email Generator API")

class ExtractJobRequest(BaseModel):
    url: str

class EmailRequest(BaseModel):
    job_data: dict  # keys: role, experience, skills, description
    techstack: str
    portfolio_link: str
    recipient_name: str
    industry: str
    tone: str

# --- Portfolio Setup ---
client = chromadb.PersistentClient("vectorstore")
collection = client.get_or_create_collection(name="portfolio")
portfolio_csv_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "../../my_portfolio.csv")
portfolio_df = pd.read_csv(portfolio_csv_path)
if not collection.count():
    for _, row in portfolio_df.iterrows():
        collection.add(
            documents=row["Techstack"],
            metadatas={"links": row["Links"]},
            ids=[str(uuid.uuid4())]
        )

def get_portfolio_links(query_text: str) -> str:
    query_results = collection.query(query_texts=[query_text], n_results=2)
    links_metadata = query_results.get("metadatas", [])
    flat_links = []
    for sub in links_metadata:
        if isinstance(sub, list):
            flat_links.extend(sub)
        else:
            flat_links.append(sub)
    return ", ".join([item.get("links", "") for item in flat_links])

# --- Initialize the Chain and LLM ---
chain = Chain()

# New endpoint: Extract Job from URL
@app.post("/extract_job")
def extract_job(request: ExtractJobRequest):
    try:
        loader = WebBaseLoader([request.url])
        loaded_docs = loader.load()
        if not loaded_docs:
            raise ValueError("No documents loaded. Please check the URL.")
        page_data = loaded_docs.pop().page_content
        # Clean the text if needed (optional)
        cleaned_text = re.sub(r'\s+', ' ', page_data).strip()
        jobs = chain.extract_jobs(cleaned_text)
        # Return the first extracted job (for simplicity)
        if not jobs:
            raise ValueError("No job details extracted.")
        return {"job_details": jobs[0]}
    except Exception as e:
        print("Error in /extract_job:", str(e))
        raise HTTPException(status_code=500, detail=str(e))

# Endpoint: Generate Cold Email using extracted job details and recipient info
@app.post("/generate_email")
def generate_email(request: EmailRequest):
    try:
        job_data = request.job_data
        role = job_data.get("role", "N/A")
        experience = job_data.get("experience", "N/A")
        skills = job_data.get("skills", "N/A")
        # If skills is a list, convert it to a comma-separated string
        if isinstance(skills, list):
            skills = ", ".join(skills)
        description = job_data.get("description", "N/A")
        
        # Query portfolio links based on skills, or fallback to provided portfolio_link
        retrieved_links = get_portfolio_links(skills)
        link_list = retrieved_links if retrieved_links else request.portfolio_link
        
        email_content = chain.write_mail(
            job={
                "role": role,
                "experience": experience,
                "skills": skills,
                "description": description
            },
            links=link_list,
            recipient_name=request.recipient_name,
            industry=request.industry,
            tone=request.tone
        )
        return {"generated_email": email_content}
    except Exception as e:
        print("Error in /generate_email:", str(e))
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/")
def read_root():
    return {"message": "Welcome to the GenAI Cold Email Generator API. Use /extract_job and /generate_email endpoints."}
