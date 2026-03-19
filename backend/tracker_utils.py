import requests
import datetime
from datetime import timezone
from backend.llm_service import calculate_job_match_score
from backend.database import get_profile_by_id

def fetch_greenhouse_jobs(company, location):
    """
    Fetches jobs for a given company using the Greenhouse Job Board API.
    Filters the jobs by location (substring match) and date (last 30 days).
    """
    board_token = company.lower().strip().replace(' ', '')
    url = f"https://boards-api.greenhouse.io/v1/boards/{board_token}/jobs?content=true"
    
    headers = {
        "Accept": "application/json"
    }

    try:
        response = requests.get(url, headers=headers, timeout=10)
        if response.status_code != 200:
            print(f"Greenhouse board not found or unavailable for token: {board_token}")
            return []

        data = response.json()
        jobs_list = data.get("jobs", [])
        
        filtered_jobs = []
        loc_search = location.lower().strip()
        
        # Determine exactly 30 days ago
        now = datetime.datetime.now(timezone.utc)
        thirty_days_ago = now - datetime.timedelta(days=30)
        
        for job in jobs_list:
            # 1. Check Location
            job_loc = job.get("location", {}).get("name", "")
            if loc_search and loc_search not in job_loc.lower():
                continue
            
            # 2. Check Date (updated_at is usually ISO 8601 with timezone like 2024-03-01T12:00:00-05:00)
            updated_at_str = job.get("updated_at")
            job_date = None
            if updated_at_str:
                try:
                    # fromisoformat requires python 3.7+ and handles most timezone formats
                    # if the string has a 'Z', replace with +00:00
                    clean_date_str = updated_at_str.replace("Z", "+00:00")
                    job_date = datetime.datetime.fromisoformat(clean_date_str)
                    
                    if job_date.tzinfo is None:
                        job_date = job_date.replace(tzinfo=timezone.utc)
                        
                    if job_date < thirty_days_ago:
                        continue
                except Exception as eval_date_err:
                    print(f"Error parsing date {updated_at_str}: {eval_date_err}")
                    pass # If we can't parse Date, include it anyway
                    
            title = job.get("title", "Unknown Title")
            job_url = job.get("absolute_url", "")
            if not job_url:
                job_url = f"https://boards.greenhouse.io/{board_token}"
                
            formatted_date = job_date.strftime("%Y-%m-%d") if job_date else "Recently"

            job_html_content = job.get("content", "")
            from bs4 import BeautifulSoup
            job_desc_clean = BeautifulSoup(job_html_content, "html.parser").get_text(separator=' ', strip=True) if job_html_content else "View details on Greenhouse"
            # Cap at 4000 characters to keep LLM context small
            job_desc_clean = job_desc_clean[:4000]
            
            filtered_jobs.append({
                "title": title,
                "company": company,
                "location": job_loc,
                "description": job_desc_clean,
                "date": formatted_date,
                "url": job_url
            })
            
        return filtered_jobs

    except Exception as e:
        print(f"Error fetching from Greenhouse: {e}")
        return []

def track_company_jobs(companies_str, locations_str, profile_id=None):
    companies = [c.strip() for c in companies_str.split(',') if c.strip()]
    locations = [l.strip() for l in locations_str.split(',') if l.strip()]
    
    all_jobs = []
    
    for company in companies:
        for location in locations:
            print(f"Tracking {company} in {location} via Greenhouse API...")
            jobs = fetch_greenhouse_jobs(company, location)
            all_jobs.extend(jobs)
            
    # Remove duplicates and sort by company name
    unique_jobs = {}
    for j in all_jobs:
        key = f"{j.get('company')}-{j.get('title')}-{j.get('location')}"
        if key not in unique_jobs:
            unique_jobs[key] = j
            
    unique_jobs_list = list(unique_jobs.values())
    
    if profile_id:
        profile = get_profile_by_id(profile_id)
        if profile:
            profile_text = profile.get("parsed_markdown", profile.get("original_text", ""))
            if profile_text:
                for j in unique_jobs_list:
                    print(f"Scoring {j.get('title')} at {j.get('company')}...")
                    j['match_score'] = calculate_job_match_score(
                        job_title=j.get('title', ''),
                        job_description=j.get('description', ''),
                        profile_text=profile_text
                    )
                return sorted(unique_jobs_list, key=lambda x: (-x.get('match_score', 0), x.get('company', ''), x.get('location', ''), x.get('title', '')))

    return sorted(unique_jobs_list, key=lambda x: (x.get('company', ''), x.get('location', ''), x.get('title', '')))
