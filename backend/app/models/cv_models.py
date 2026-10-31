from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel


class RunnerUpCategory(BaseModel):
    category: str
    confidence: float


class CVOut(BaseModel):
    id: str
    user_id: str
    file_name: str
    file_type: str
    upload_date: datetime
    analysed: bool = False
    predicted_category: Optional[str] = None
    confidence: Optional[float] = None
    runner_up_categories: List[RunnerUpCategory] = []
