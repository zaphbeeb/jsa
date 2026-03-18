import os
try:
    from google import genai
except ImportError:
    genai = None
from dotenv import load_dotenv
dotenv_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), '.env')
load_dotenv(dotenv_path)
def parse_resume_with_llm(resume_text: str) -> str:
    api_key = os.environ.get("GEMINI_API_KEY")
    if not api_key:
        return "Error: GEMINI_API_KEY environment variable not set. Please set it in a .env file to use the AI parsing feature."

    if not genai:
        return "Error: google-genai package not installed."

    try:
        client = genai.Client(api_key=api_key)
        
        prompt = """
        You are an expert technical recruiter and resume parser.
        Please carefully read the following resume text and extract the key skills and experience of the individual.
        Format your response purely in Markdown. Use headers, bullet points, and bold text for readability.
        
        Your response should include:
        1. An executive summary of the candidate's profile.
        2. A distinct section listing all Technical and Soft Skills.
        3. A clear chronological breakdown of their Work Experience, including company names, roles, duration, and key accomplishments.
        4. Education and Certifications.
        
        IMPORTANT: Provide ONLY the requested markdown report without conversational filler.

        Resume Text:
        ---
        {text}
        """
        
        response = client.models.generate_content(
            model='gemini-2.5-flash',
            contents=prompt.format(text=resume_text),
        )
        return response.text
    except Exception as e:
        return f"Error communicating with Gemini API: {str(e)}"
