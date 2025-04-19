from pydantic import BaseModel, Field
from typing import Optional

class MovieBase(BaseModel):
    title: str = Field(..., min_length=1, max_length=200)
    genre: str = Field(..., min_length=1)
    release_year: int = Field(..., ge=1900)
    duration: int = Field(..., ge=1)
    description: str = Field(..., min_length=10)

class MovieResponse(MovieBase):
    id: int

    class Config:
        orm_mode = True

class MovieRecommendation(MovieResponse):
    predicted_rating: Optional[float] = None
    similarity_score: Optional[float] = None
    cluster_id: Optional[int] = None 