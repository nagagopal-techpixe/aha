from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime
class ReviewBase(BaseModel):
    title: str
    content: str
    image_url: Optional[str] = None
    meta_description: Optional[str]
    focus_keyword: Optional[str]
    seo_tags: Optional[List[str]] = []

class ReviewResponse(ReviewBase):
    id: str
    created_at: datetime