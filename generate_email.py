import uuid
import chromadb
import pandas as pd
from langchain_core.prompts import PromptTemplate
from langchain_groq import ChatGroq

# ------------------------------
# 1. Setup Portfolio Vector Store
# ------------------------------
client = chromadb.PersistentClient("vectorstore")
collection = client.get_or_create_collection(name="portfolio")

# Load portfolio CSV data (create your own CSV with your custom data)
portfolio_df = pd.read_csv("my_portfolio.csv")  # Ensure this file exists in your project root

if not collection.count():
    for _, row in portfolio_df.iterrows():
        collection.add(
            documents=row["Techstack"],
            metadatas={"links": row["Links"]},
            ids=[str(uuid.uuid4())]
        )

def get_portfolio_links(query_text: str) -> str:
    query_results = collection.query(query_texts=[query_text], n_results=2)
    # Flatten results if needed
    links_metadata = query_results.get("metadatas", [])
    flat_links = []
    for sub in links_metadata:
        if isinstance(sub, list):
            flat_links.extend(sub)
        else:
            flat_links.append(sub)
    link_list = ", ".join([item.get("links", "") for item in flat_links])
    return link_list

# ------------------------------
# 2. Prepare Job Data (Sample)
# ------------------------------
job = {
    "role": "Data Scientist",
    "experience": "3-5 years",
    "skills": "Python, SQL, Machine Learning",
    "description": "Responsible for analyzing data and building predictive models."
}

# ------------------------------
# 3. Query Portfolio for Relevant Links
# ------------------------------
link_list = get_portfolio_links(job["skills"])
print("Retrieved portfolio links:", link_list)

# ------------------------------
# 4. Generate the Cold Email Using a Prompt Template
# ------------------------------
llm = ChatGroq(
    temperature=0,
    groq_api_key="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",  # Replace with your valid API key
    model_name="llama-3.2-90b-vision-preview"       # Use the supported model name
)

# Define a prompt template that includes our additional fields.
prompt_email = PromptTemplate.from_template(
    """
    You are Asad, a Business Development Executive at AIKHAN, an AI & Software Consulting company.

    JOB DETAILS:
    Role: {role}
    Experience: {experience}
    Skills: {skills}
    Description: {description}

    PORTFOLIO LINKS:
    {link_list}

    RECIPIENT DETAILS:
    Recipient Name: {recipient_name}
    Industry: {industry}
    Tone: {tone}

    INSTRUCTION:
    Write a cold email in the exact format below and do not include any additional text:
    
    Subject: <short, compelling subject line>
    Greeting: <personalized greeting addressing the recipient by name>
    Body: <the main email content referencing the job details and portfolio links>
    Closing: <a clear call-to-action and closing statement>
    Signature: <your name, your role, and your company>

    Return ONLY the email content in this structure.
    """
)

chain_email = prompt_email | llm
# ------------------------------
# NEW: Define a helper function for generating the cold email
# ------------------------------
def generate_cold_email(recipient_name="Hiring Manager", industry="Healthcare", tone="professional and friendly"):
    # Use the existing sample job defined earlier
    sample_job = job
    
    # Query portfolio for relevant links based on the sample job's skills
    link_list = get_portfolio_links(sample_job["skills"])
    
    email_response = chain_email.invoke({
        "role": sample_job["role"],
        "experience": sample_job["experience"],
        "skills": sample_job["skills"],
        "description": sample_job["description"],
        "link_list": link_list if link_list else "https://example.com/portfolio",
        "recipient_name": recipient_name,
        "industry": industry,
        "tone": tone
    })
    return email_response.content

# ------------------------------
# Test the function in the __main__ block
# ------------------------------
if __name__ == '__main__':
    generated_email = generate_cold_email()
    print("\nGenerated Cold Email:")
    print(generated_email)
