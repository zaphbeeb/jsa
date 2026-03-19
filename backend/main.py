from fastapi import FastAPI, UploadFile, File, Form, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pydantic import BaseModel
import os

from backend.database import init_db, save_profile, get_profiles, get_profile_by_id, update_profile, delete_profile
from backend.parse_utils import parse_file
from backend.llm_service import parse_resume_with_llm
from backend.tracker_utils import track_company_jobs

app = FastAPI(title="Resume Parser AI")

# Allow CORS for frontend dev if needed
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize database
init_db()

# Serve frontend static files
frontend_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "frontend")
if not os.path.exists(frontend_dir):
    os.makedirs(frontend_dir)

app.mount("/static", StaticFiles(directory=frontend_dir), name="static")

@app.get("/")
def read_index():
    index_path = os.path.join(frontend_dir, "index.html")
    if os.path.exists(index_path):
        return FileResponse(index_path)
    return {"message": "Frontend not found. Please create an index.html in the frontend folder."}

class ParseTextRequest(BaseModel):
    text: str

@app.post("/api/parse/file")
async def parse_uploaded_file(file: UploadFile = File(...)):
    contents = await file.read()
    extracted_text = parse_file(file.filename, contents)
    
    if not extracted_text.strip():
        raise HTTPException(status_code=400, detail="Could not extract text from the file.")
        
    markdown_result = parse_resume_with_llm(extracted_text)
    
    return {
        "filename": file.filename,
        "extracted_text": extracted_text,
        "markdown_result": markdown_result
    }

@app.post("/api/parse/text")
async def parse_raw_text(request: ParseTextRequest):
    if not request.text.strip():
        raise HTTPException(status_code=400, detail="Provided text is empty.")
        
    markdown_result = parse_resume_with_llm(request.text)
    
    return {
        "extracted_text": request.text,
        "markdown_result": markdown_result
    }

class SaveProfileRequest(BaseModel):
    name: str
    original_text: str
    parsed_markdown: str

@app.post("/api/profiles")
async def create_profile(request: SaveProfileRequest):
    if not request.name.strip():
        raise HTTPException(status_code=400, detail="Profile name cannot be empty.")
        
    profile_id = save_profile(request.name, request.original_text, request.parsed_markdown)
    return {"id": profile_id, "message": "Profile saved successfully"}

@app.get("/api/profiles")
async def list_profiles():
    return get_profiles()

@app.get("/api/profiles/{profile_id}")
async def get_profile(profile_id: int):
    profile = get_profile_by_id(profile_id)
    if not profile:
        raise HTTPException(status_code=404, detail="Profile not found")
    return profile

class UpdateProfileNameRequest(BaseModel):
    name: str

@app.put("/api/profiles/{profile_id}")
async def update_profile_endpoint(profile_id: int, request: UpdateProfileNameRequest):
    if not request.name.strip():
        raise HTTPException(status_code=400, detail="Profile name cannot be empty.")
    
    profile = get_profile_by_id(profile_id)
    if not profile:
        raise HTTPException(status_code=404, detail="Profile not found")
        
    update_profile(profile_id, request.name)
    return {"message": "Profile updated successfully"}

@app.delete("/api/profiles/{profile_id}")
async def delete_profile_endpoint(profile_id: int):
    profile = get_profile_by_id(profile_id)
    if not profile:
        raise HTTPException(status_code=404, detail="Profile not found")
        
    delete_profile(profile_id)
    return {"message": "Profile deleted successfully"}

from typing import Optional

class TrackJobsRequest(BaseModel):
    locations: str
    companies: str
    profile_id: Optional[int] = None

@app.post("/api/track")
async def track_jobs_endpoint(request: TrackJobsRequest):
    if not request.locations.strip() or not request.companies.strip():
        raise HTTPException(status_code=400, detail="Locations and companies cannot be empty.")
    
    try:
        jobs = track_company_jobs(request.companies, request.locations)
        return jobs
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
