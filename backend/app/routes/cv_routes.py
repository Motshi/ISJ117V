"""
FR3: CV Upload and Management
FR4/FR5: CV Analysis using our trained model (runs automatically on upload)

Endpoints:
  POST   /api/cv/upload    - upload a PDF/DOCX CV, analysed immediately (auth required)
  GET    /api/cv           - list the current user's uploaded CVs
  DELETE /api/cv/{cv_id}   - remove a CV
"""
import uuid
from datetime import datetime, timezone
from pathlib import Path

from bson import ObjectId
from fastapi import APIRouter, Depends, HTTPException, UploadFile, status
from app.services.job_search_service import search_jobs_pages

from app.core.config import settings
from app.core.security import get_current_user_id
from app.database import cvs_collection
from app.models.cv_models import CVOut
from app.services.cv_analysis_service import analyse_cv
from app.services.job_search_service import search_jobs_pages

router = APIRouter(prefix="/api/cv", tags=["CV"])

ALLOWED_CONTENT_TYPES = {
    "application/pdf": ".pdf",
    "application/vnd.openxmlformats-officedocument.wordprocessingml.document": ".docx",
}


def _cv_doc_to_out(doc: dict) -> CVOut:
    return CVOut(
        id=str(doc["_id"]),
        user_id=doc["user_id"],
        file_name=doc["file_name"],
        file_type=doc["file_type"],
        upload_date=doc["upload_date"],
        analysed=doc.get("analysed", False),
        predicted_category=doc.get("predicted_category"),
        confidence=doc.get("confidence"),
        runner_up_categories=doc.get("runner_up_categories", []),
    )


@router.post("/upload", response_model=CVOut, status_code=status.HTTP_201_CREATED)
async def upload_cv(
    file: UploadFile,
    current_user_id: str = Depends(get_current_user_id),
):
    if file.content_type not in ALLOWED_CONTENT_TYPES:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Only PDF and DOCX files are accepted",
        )

    contents = await file.read()
    max_bytes = settings.max_cv_size_mb * 1024 * 1024
    if len(contents) > max_bytes:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"File too large. Max size is {settings.max_cv_size_mb}MB",
        )

    extension = ALLOWED_CONTENT_TYPES[file.content_type]
    file_type = extension.lstrip(".")
    user_dir = Path(settings.cv_upload_dir) / current_user_id
    user_dir.mkdir(parents=True, exist_ok=True)
    stored_filename = f"{uuid.uuid4().hex}{extension}"
    file_path = user_dir / stored_filename

    with open(file_path, "wb") as f:
        f.write(contents)

    # Only one CV per user at a time: remove any previous CV (record + file)
    # before saving the new one, so uploading a fresh CV replaces the old
    # one instead of accumulating a growing list.
    old_cvs = cvs_collection.find({"user_id": current_user_id})
    async for old_cv in old_cvs:
        old_path = Path(old_cv["file_path"])
        if old_path.exists():
            old_path.unlink()
    await cvs_collection.delete_many({"user_id": current_user_id})

    # Run the uploaded CV through our trained model right away.
    analysis = analyse_cv(str(file_path), file_type)

    cv_doc = {
        "user_id": current_user_id,
        "file_name": file.filename,
        "file_path": str(file_path),
        "file_type": file_type,
        "upload_date": datetime.now(timezone.utc),
        "analysed": analysis.get("predicted_category") is not None,
        "predicted_category": analysis.get("predicted_category"),
        "confidence": analysis.get("confidence"),
        "runner_up_categories": analysis.get("runner_up_categories", []),
    }
    result = await cvs_collection.insert_one(cv_doc)
    cv_doc["_id"] = result.inserted_id
    return _cv_doc_to_out(cv_doc)


@router.get("", response_model=list[CVOut])
async def list_cvs(current_user_id: str = Depends(get_current_user_id)):
    cursor = cvs_collection.find({"user_id": current_user_id}).sort("upload_date", -1)
    return [_cv_doc_to_out(doc) async for doc in cursor]


@router.delete("/{cv_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_cv(cv_id: str, current_user_id: str = Depends(get_current_user_id)):
    cv_doc = await cvs_collection.find_one({"_id": ObjectId(cv_id), "user_id": current_user_id})
    if not cv_doc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="CV not found")

    file_path = Path(cv_doc["file_path"])
    if file_path.exists():
        file_path.unlink()

    await cvs_collection.delete_one({"_id": ObjectId(cv_id)})


@router.get("/{cv_id}/skill-gaps")
async def get_skill_gaps(cv_id: str, current_user_id: str = Depends(get_current_user_id)):
    from app.services.skill_gap_service import find_skill_gaps
    from app.services.job_search_service import search_jobs
    from app.services.matching_service import score_jobs_against_cv
    from app.services.cv_analysis_service import extract_text

    cv_doc = await cvs_collection.find_one({"_id": ObjectId(cv_id), "user_id": current_user_id})
    if not cv_doc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="CV not found")
    if not cv_doc.get("predicted_category"):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="This CV hasn't been analysed yet")

    cv_text = extract_text(cv_doc["file_path"], cv_doc["file_type"])

    try:
        jobs = await search_jobs_pages(keywords=cv_doc["predicted_category"].replace("-", " "))
    except Exception as e:
        print(f"[skill-gaps] job fetch failed: {repr(e)}", flush=True)
        jobs = []

    scored_jobs = score_jobs_against_cv(cv_text, jobs) if jobs else []
    gaps = find_skill_gaps(cv_text, scored_jobs)

    return {
        "predicted_category": cv_doc["predicted_category"],
        "jobs_analysed": len(scored_jobs),
        "skill_gaps": gaps,
    }