from typing import Optional

from pydantic import BaseModel


class JobOut(BaseModel):
    id: str
    title: str
    company: str
    location: str
    description: str
    salary_min: Optional[float] = None
    salary_max: Optional[float] = None
    url: str
    posted_date: Optional[str] = None
    match_score: Optional[int] = None
    auto_applied: bool = False
