# chains.py
import os
from langchain_groq import ChatGroq
from langchain_core.prompts import PromptTemplate
from langchain_core.output_parsers import JsonOutputParser
from langchain_core.exceptions import OutputParserException
from dotenv import load_dotenv

load_dotenv()

DEFAULT_MODEL = "llama-3.2-90b-vision-preview"


def build_llm():
    """Create the Groq chat model from environment variables (see .env.example)."""
    api_key = os.getenv("GROQ_API_KEY")
    if not api_key:
        raise RuntimeError("GROQ_API_KEY is not set. Copy .env.example to .env and add your key.")
    return ChatGroq(
        temperature=0,
        groq_api_key=api_key,
        model_name=os.getenv("GROQ_MODEL", DEFAULT_MODEL),
    )

class Chain:
    def __init__(self):
        self.llm = build_llm()

    def extract_jobs(self, cleaned_text):
        prompt_extract = PromptTemplate.from_template(
            """
            ### SCRAPED TEXT FROM WEBSITE:
            {page_data}
            ### INSTRUCTION:
            The scraped text is from the career's page of a website.
            Your job is to extract the job postings and return them in JSON format containing the following keys: `role`, `experience`, `skills` and `description`.
            Only return the valid JSON.
            ### VALID JSON (NO PREAMBLE):
            """
        )
        chain_extract = prompt_extract | self.llm 
        res = chain_extract.invoke(input={"page_data": cleaned_text})
        try:
            json_parser = JsonOutputParser()
            res = json_parser.parse(res.content)
        except OutputParserException:
            raise OutputParserException("Context too big. Unable to parse jobs.")
        return res if isinstance(res, list) else [res]

    def write_mail(self, job, links, recipient_name, industry, tone):
        prompt_email = PromptTemplate.from_template(
            """
            ### JOB DESCRIPTION:
            {job_description}
            
            ### RECIPIENT DETAILS:
            Recipient Name: {recipient_name}
            Industry: {industry}
            Tone: {tone}
            
            ### INSTRUCTION:
            You are Asad, a business development executive at AIKHAN. AIKHAN is an AI & Software Consulting company dedicated to facilitating
            the seamless integration of business processes through automated tools. Your task is to write a cold email to the client regarding the job described above, highlighting AIKHAN's capabilities.
            Also, incorporate the most relevant portfolio links: {link_list}.
            Do not provide any preamble.
            ### EMAIL (NO PREAMBLE):
            """
        )
        chain_email = prompt_email | self.llm 
        res = chain_email.invoke({
            "job_description": str(job),
            "link_list": links,
            "recipient_name": recipient_name,
            "industry": industry,
            "tone": tone
        })
        return res.content

if __name__ == "__main__":
    print("GROQ_API_KEY set:", bool(os.getenv("GROQ_API_KEY")))
