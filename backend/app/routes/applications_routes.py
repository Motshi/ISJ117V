"""
FR8: Automated Application Submission
FR9: Application Tracking & Status Updates

Endpoints:
  POST /api/applications          - submit an application (manual or auto)
  GET  /api/applications          - list the current user's applications
  GET  /api/applications/{app_id} - get one application's full timeline
  PUT  /api/applications/{app_id}/status - update status (simulates a real
                                             status change, e.g. employer response)

Auto-apply logic: the platform doesn't silently apply on a schedule by
itself (that would need a background job scheduler, out of scope here) —
instead, the frontend checks the user's saved auto-apply threshold
(Profile) against a job's match_score, and if it clears the bar, calls this
same endpoint with source="auto" instead of source="manual". Either way,
every application is recorded identically here, distinguished only by the
'source' field — which is exactly what FR8 requires: automated submission
for jobs that meet the user's criteria, without them clicking manually.
"""
from datetime import datetime, timezone

from bson import ObjectId
from bson.errors import InvalidId
from fastapi import APIRouter, Depends, HTTPException, status

from app.core.security import get_current_user_id
from app.database import applications_collection
from app.models.application_models import ApplicationCreate, ApplicationOut, TimelineStep

router = APIRouter(prefix="/api/applications", tags=["Applications"])


def _initial_timeline(source: str) -> list[dict]:
    label = "Auto-logged (matched your threshold)" if source == "auto" else "Application submitted by you"
    today = datetime.now(timezone.utc).strftime("%d %b %Y")
    return [
        {"label": label, "date": today, "done": True},
        {"label": "Under review", "date": None, "done": False},
        {"label": "Interview stage", "date": None, "done": False},
        {"label": "Decision", "date": None, "done": False},
    ]


def _app_doc_to_out(doc: dict) -> ApplicationOut:
    return ApplicationOut(
        id=str(doc["_id"]),
        user_id=doc["user_id"],
        job_id=doc["job_id"],
        job_title=doc["job_title"],
        company=doc["company"],
        job_url=doc["job_url"],
        match_score=doc.get("match_score"),
        source=doc.get("source", "manual"),
        status=doc.get("status", "Pending"),
        applied_date=doc["applied_date"],
        timeline=[TimelineStep(**step) for step in doc.get("timeline", [])],
    )


@router.post("", response_model=ApplicationOut, status_code=status.HTTP_201_CREATED)
async def submit_application(
    payload: ApplicationCreate,
    current_user_id: str = Depends(get_current_user_id),
):
    existing = await applications_collection.find_one({
        "user_id": current_user_id,
        "job_id": payload.job_id,
    })
    if existing:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="You've already applied to this job.",
        )

    app_doc = {
        "user_id": current_user_id,
        "job_id": payload.job_id,
        "job_title": payload.job_title,
        "company": payload.company,
        "job_url": payload.job_url,
        "match_score": payload.match_score,
        "source": payload.source,
        "status": "Submitted" if payload.source == "auto" else "Pending",
        "applied_date": datetime.now(timezone.utc),
        "timeline": _initial_timeline(payload.source),
    }
    result = await applications_collection.insert_one(app_doc)
    app_doc["_id"] = result.inserted_id
    return _app_doc_to_out(app_doc)


@router.get("", response_model=list[ApplicationOut])
async def list_applications(current_user_id: str = Depends(get_current_user_id)):
    cursor = applications_collection.find({"user_id": current_user_id}).sort("applied_date", -1)
    return [_app_doc_to_out(doc) async for doc in cursor]


@router.get("/{app_id}", response_model=ApplicationOut)
async def get_application(app_id: str, current_user_id: str = Depends(get_current_user_id)):
    doc = await _get_app_or_404(app_id, current_user_id)
    return _app_doc_to_out(doc)


@router.put("/{app_id}/status", response_model=ApplicationOut)
async def update_status(
    app_id: str,
    new_status: str,
    current_user_id: str = Depends(get_current_user_id),
):
    doc = await _get_app_or_404(app_id, current_user_id)

    valid_statuses = {"Pending", "Submitted", "Under Review", "Interview", "Successful", "Unsuccessful"}
    if new_status not in valid_statuses:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Status must be one of: {', '.join(sorted(valid_statuses))}",
        )

    today = datetime.now(timezone.utc).strftime("%d %b %Y")
    timeline = doc.get("timeline", [])
    status_to_step = {
        "Under Review": 1, "Interview": 2, "Successful": 3, "Unsuccessful": 3,
    }
    if new_status in status_to_step:
        idx = status_to_step[new_status]
        if idx < len(timeline):
            timeline[idx]["done"] = True
            timeline[idx]["date"] = today
            if new_status == "Unsuccessful":
                timeline[idx]["label"] = "Decision: not selected"
            elif new_status == "Successful":
                timeline[idx]["label"] = "Decision: successful"

    await applications_collection.update_one(
        {"_id": ObjectId(app_id)},
        {"$set": {"status": new_status, "timeline": timeline}},
    )
    updated_doc = await applications_collection.find_one({"_id": ObjectId(app_id)})
    return _app_doc_to_out(updated_doc)


async def _get_app_or_404(app_id: str, user_id: str) -> dict:
    try:
        oid = ObjectId(app_id)
    except InvalidId:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid application id")
    doc = await applications_collection.find_one({"_id": oid, "user_id": user_id})
    if not doc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Application not found")
    return doc
