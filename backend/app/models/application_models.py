from datetime import datetime
from typing import Optional

from pydantic import BaseModel


class ApplicationCreate(BaseModel):
    job_id: str
    job_title: str
    company: str
    job_url: str
    match_score: Optional[int] = None
    source: str = "manual"  # "manual" or "auto"


class TimelineStep(BaseModel):
    label: str
    date: Optional[str] = None
    done: bool = False


class ApplicationOut(BaseModel):
    id: str
    user_id: str
    job_id: str
    job_title: str
    company: str
    job_url: str
    match_score: Optional[int] = None
    source: str
    status: str
    applied_date: datetime
    timeline: list[TimelineStep] = []
