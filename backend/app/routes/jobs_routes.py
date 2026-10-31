"""
FR6: Live Job Listings Retrieval
FR7: AI-Based CV–Job Compatibility Scoring
FR8: Automated Application Submission

Endpoints:
  GET /api/jobs/search?keywords=...&location=...&cv_id=... — live jobs from
  Adzuna, optionally scored against a specific uploaded CV. If cv_id is
  given, any job that clears the user's saved auto-apply threshold
  (Profile -> minimum_match_score) is AUTOMATICALLY logged as an
  application right here — no click required. Jobs below the threshold
  still appear in the results for manual "Apply".

Honest scope note: this platform cannot submit a real application on an
external site on the user's behalf — no job-listings API (including
Adzuna) exposes that capability, and doing it via browser automation
across arbitrary employer websites is outside this project's scope.
What IS implemented, honestly: automatic detection and recording of which
jobs the user qualifies for, the moment they're found — distinguishing
these from manually-applied jobs via the 'source' field.
"""
from datetime import datetime, timezone
import time
from bson import ObjectId
from fastapi import APIRouter, Depends, HTTPException, Query, status

from app.core.security import get_current_user_id
from app.database import applications_collection, cvs_collection, users_collection
from app.models.job_models import JobOut
from app.services.cv_analysis_service import extract_text
from app.services.job_search_service import search_jobs
from app.services.matching_service import score_jobs_against_cv

router = APIRouter(prefix="/api/jobs", tags=["Jobs"])


def _initial_timeline() -> list[dict]:
    today = datetime.now(timezone.utc).strftime("%d %b %Y")
    return [
        {"label": "Auto-logged (matched your threshold)", "date": today, "done": True},
        {"label": "Under review", "date": None, "done": False},
        {"label": "Interview stage", "date": None, "done": False},
        {"label": "Decision", "date": None, "done": False},
    ]


@router.get("/search", response_model=list[JobOut])
async def search(
    keywords: str = Query(..., description="e.g. 'Information Technology', 'Software Developer'"),
    location: str = Query("", description="e.g. 'Pretoria', 'Johannesburg'"),
    cv_id: str = Query(None, description="Optional: score against this CV and enable auto-apply"),
    current_user_id: str = Depends(get_current_user_id),
):

    t0 = time.perf_counter()
    try:
        jobs = await search_jobs(keywords=keywords, location=location)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"Could not reach the job listings service: {e}",
        )
    
    print(f"[timing] adzuna: {time.perf_counter()-t0:.1f}s", flush=True)
    if cv_id:
        cv_doc = await cvs_collection.find_one({"_id": ObjectId(cv_id), "user_id": current_user_id})
        if not cv_doc:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="CV not found")
        cv_text = extract_text(cv_doc["file_path"], cv_doc["file_type"])
        jobs = score_jobs_against_cv(cv_text, jobs)

        # FR8: auto-apply — check the user's saved threshold and log
        # qualifying jobs as applications automatically.
        user_doc = await users_collection.find_one({"_id": ObjectId(current_user_id)})
        threshold = user_doc.get("minimum_match_score") if user_doc else None

        if threshold is not None:
            for job in jobs:
                if job.get("match_score", 0) < threshold:
                    continue
                already_applied = await applications_collection.find_one({
                    "user_id": current_user_id,
                    "job_id": job["id"],
                })
                if already_applied:
                    job["auto_applied"] = True
                    continue
                await applications_collection.insert_one({
                    "user_id": current_user_id,
                    "job_id": job["id"],
                    "job_title": job["title"],
                    "company": job["company"],
                    "job_url": job["url"],
                    "match_score": job.get("match_score"),
                    "source": "auto",
                    "status": "Submitted",
                    "applied_date": datetime.now(timezone.utc),
                    "timeline": _initial_timeline(),
                })
                job["auto_applied"] = True
        print(f"[timing] total: {time.perf_counter()-t0:.1f}s", flush=True)
    return jobs
