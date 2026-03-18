import requests
from bs4 import BeautifulSoup
import os
import json
from google import genai
from dotenv import load_dotenv

load_dotenv()

def get_gemini_client():
    api_key = os.environ.get("GEMINI_API_KEY")
    if not api_key:
        return None
    return genai.Client(api_key=api_key)

def search_careers_page(company, location):
    """
    Simulates finding a careers page. 
    In a real app, you'd use a Search API (like Google Custom Search) or a scraper for DuckDuckGo.
    For this demo, we'll use a search-like query to a public search engine or just try common patterns.
    """
    # For now, we'll use a search query approach if we had an API.
    # Since we're building a 'premium' demo, we'll try to find the site via DuckDuckGo.
    search_url = f"https://duckduckgo.com/html/?q={company}+careers+{location}"
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
    }
    
    try:
        response = requests.get(search_url, headers=headers, timeout=10)
        if response.status_code == 200:
            soup = BeautifulSoup(response.text, 'html.parser')
            # Look for the first few result links
            links = soup.find_all('a', class_='result__a', href=True)
            if links:
                return links[0]['href']
    except Exception as e:
        print(f"Search failed: {e}")
    
    # Fallback to a guessed URL
    return f"https://www.{company.lower().replace(' ', '')}.com/careers"

def scrape_job_info(url, company, location):
    """
    Scrapes the given URL and uses Gemini to extract job details.
    """
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
    }
    
    try:
        response = requests.get(url, headers=headers, timeout=15)
        if response.status_code != 200:
            return []
        
        soup = BeautifulSoup(response.text, 'html.parser')
        # Remove scripts and styles
        for script in soup(["script", "style"]):
            script.decompose()
            
        page_text = soup.get_text(separator=' ', strip=True)[:10000] # Cap at 10k chars
        
        client = get_gemini_client()
        if not client:
            return []
            
        prompt = f"""
        You are an expert job scraper. I will provide you with the text content of a company's career page.
        Your task is to extract all open job positions that match the location: '{location}'.
        
        Company: {company}
        Location requested: {location}
        
        For each matching job, provide:
        - title: The role title
        - company: {company}
        - location: The specific location mentioned (should be in or near {location})
        - description: A short 1-2 sentence summary of the role
        - date: Date posted (if available, otherwise leave null)
        - url: The original URL provided: {url}
        
        Format your response as a JSON list of objects. If no jobs match, return an empty list [].
        Do NOT include any conversational filler.
        
        Career Page Text:
        ---
        {page_text}
        """
        
        response = client.models.generate_content(
            model='gemini-2.0-flash',
            contents=prompt,
        )
        
        # Extract JSON from response
        text = response.text.strip()
        if "```json" in text:
            text = text.split("```json")[1].split("```")[0].strip()
        elif "```" in text:
            text = text.split("```")[1].split("```")[0].strip()
            
        return json.loads(text)
        
    except Exception as e:
        print(f"Scraping failed for {url}: {e}")
        return []

def track_company_jobs(companies_str, locations_str):
    companies = [c.strip() for c in companies_str.split(',') if c.strip()]
    locations = [l.strip() for l in locations_str.split(',') if l.strip()]
    
    all_jobs = []
    
    for company in companies:
        for location in locations:
            print(f"Tracking {company} in {location}...")
            url = search_careers_page(company, location)
            jobs = scrape_job_info(url, company, location)
            all_jobs.extend(jobs)
            
    # Remove duplicates and sort by company name
    unique_jobs = { f"{j['company']}-{j['title']}-{j['location']}": j for j in all_jobs }.values()
    return sorted(list(unique_jobs), key=lambda x: (x['company'], x['location'], x['title']))
