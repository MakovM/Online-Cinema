from typing import Optional, List
from uuid import UUID

from pydantic import BaseModel, Field


class CertificationSchema(BaseModel):
    id: int
    name: str

    model_config = {
        "from_attributes": True,
    }


class GenreSchema(BaseModel):
    id: int
    name: str

    model_config = {
        "from_attributes": True,
    }


class StarSchema(BaseModel):
    id: int
    name: str

    model_config = {
        "from_attributes": True,
    }


class DirectorSchema(BaseModel):
    id: int
    name: str

    model_config = {
        "from_attributes": True,
    }


class MovieBaseSchema(BaseModel):
    name: str = Field(..., max_length=255)
    year: int = Field(..., ge=1800, le=2100)
    time: int = Field(..., gt=0, description="Duration in minutes")
    imdb: float = Field(..., ge=0.0, le=10.0)
    votes: int = Field(..., ge=0)
    meta_score: Optional[float] = Field(None, ge=0.0, le=100.0)
    gross: Optional[float] = Field(None, ge=0)
    description: str
    price: float = Field(..., ge=0)

    model_config = {"from_attributes": True}


class MovieDetailSchema(MovieBaseSchema):
    id: int
    uuid: UUID
    certification: CertificationSchema
    genres: List[GenreSchema]
    directors: List[DirectorSchema]
    stars: List[StarSchema]

    model_config = {
        "from_attributes": True,
    }


class MovieListItemSchema(BaseModel):
    id: int
    uuid: UUID
    name: str
    year: int
    time: int
    imdb: float
    price: float

    model_config = {
        "from_attributes": True,
    }


class MovieListResponseSchema(BaseModel):
    movies: List[MovieListItemSchema]
    prev_page: Optional[str]
    next_page: Optional[str]
    total_pages: int
    total_items: int

    model_config = {
        "from_attributes": True,
    }


class MovieCreateSchema(BaseModel):
    name: str = Field(..., max_length=255)
    year: int = Field(..., ge=1800, le=2100)
    time: int = Field(..., gt=0, description="Duration in minutes")
    imdb: float = Field(..., ge=0.0, le=10.0)
    votes: int = Field(..., ge=0)
    meta_score: Optional[float] = Field(None, ge=0.0, le=100.0)
    gross: Optional[float] = Field(None, ge=0)
    description: str
    price: float = Field(..., ge=0)
    certification: str
    genres: List[str]
    directors: List[str]
    stars: List[str]

    model_config = {
        "from_attributes": True,
    }


class MovieUpdateSchema(BaseModel):
    name: Optional[str] = Field(None, max_length=255)
    year: Optional[int] = Field(None, ge=1800, le=2100)
    time: Optional[int] = Field(None, gt=0)
    imdb: Optional[float] = Field(None, ge=0.0, le=10.0)
    votes: Optional[int] = Field(None, ge=0)
    meta_score: Optional[float] = Field(None, ge=0.0, le=100.0)
    gross: Optional[float] = Field(None, ge=0)
    description: Optional[str] = None
    price: Optional[float] = Field(None, ge=0)

    model_config = {
        "from_attributes": True,
    }


class GenreCreateSchema(BaseModel):
    name: str = Field(..., max_length=255)


class GenreUpdateSchema(BaseModel):
    name: Optional[str] = Field(None, max_length=255)


class StarCreateSchema(BaseModel):
    name: str = Field(..., max_length=255)


class StarUpdateSchema(BaseModel):
    name: Optional[str] = Field(None, max_length=255)
