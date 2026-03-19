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
        You are an expert technical recruiter analyzing a resume to identify key job-search actionable items.
        Please carefully read the following resume text and extract ONLY the most critical, quantifiable data points and skills relevant for job searching.
        Format your response purely in Markdown. Use headers, bullet points, and bold text for readability.

        Your extraction MUST focus on:
        1. **Quantifiable Experience**: For example, "10 years experience in Java", "Led a team of 15 engineers", or "Improved performance by 20%".
        2. **Core Technical/Hard Skills**: A concise list of programming languages, frameworks, tools, or methodologies the candidate is proficient in.
        3. **Major Achievements & Projects**: High-impact accomplishments that show value to a potential employer.
        4. **Education & Key Certifications**: Only brief mentions of relevant degrees or certs (e.g., "AWS Certified Solutions Architect", "B.S. in Computer Science").

        Do NOT just regurgitate the resume content. Do NOT include conversational filler. Synthesize the text into a highly actionable recruiter summary.
        
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

def calculate_job_match_score(job_title: str, job_description: str, profile_text: str) -> int:
    api_key = os.environ.get("GEMINI_API_KEY")
    if not api_key or not genai:
        return 0

    try:
        client = genai.Client(api_key=api_key)
        
        prompt = """
        You are an expert technical recruiter matching a candidate's resume to a job opportunity.
        Your task is to analyze the candidate's profile against the job title and description.
        
        Output ONLY a single integer between 0 and 100 representing the match score (0 = no match, 100 = perfect match).
        Do not include any explanation, just the number.

        Job Title: {title}
        Job Description: {desc}
        
        Candidate Profile:
        ---
        {profile}
        ---
        """
        
        response = client.models.generate_content(
            model='gemini-2.5-flash',
            contents=prompt.format(title=job_title, desc=job_description, profile=profile_text),
        )
        
        score_text = response.text.strip()
        import re
        match = re.search(r'\d+', score_text)
        if match:
            return min(100, max(0, int(match.group())))
        return 0
    except Exception as e:
        print(f"Error calculating score: {e}")
        return 0
