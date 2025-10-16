from datetime import datetime
from typing import Optional, List
from uuid import UUID

from pydantic import BaseModel, Field, field_validator

from schemas.examples.movies import (
    certification_schema_example,
    genre_schema_example,
    star_schema_example,
    director_schema_example,
    movie_create_schema_example,
    movie_detail_schema_example,
    movie_update_schema_example,
)


class CertificationSchema(BaseModel):
    id: int
    name: str

    model_config = {
        "from_attributes": True,
        "json_schema_extra": {"examples": [certification_schema_example]},
    }


class GenreSchema(BaseModel):
    id: int
    name: str

    model_config = {
        "from_attributes": True,
        "json_schema_extra": {"examples": [genre_schema_example]},
    }


class GenreWithCountSchema(GenreSchema):
    movie_count: int

    model_config = {
        "from_attributes": True,
        "json_schema_extra": {"examples": [{"id": 1, "name": "Action", "movie_count": 42}]},
    }


class StarSchema(BaseModel):
    id: int
    name: str

    model_config = {
        "from_attributes": True,
        "json_schema_extra": {"examples": [star_schema_example]},
    }


class DirectorSchema(BaseModel):
    id: int
    name: str

    model_config = {
        "from_attributes": True,
        "json_schema_extra": {"examples": [director_schema_example]},
    }


class MovieBaseSchema(BaseModel):
    name: str = Field(..., max_length=255)
    year: int = Field(..., ge=1800)
    time: int = Field(..., gt=0, description="Duration in minutes")
    imdb: float = Field(..., ge=0.0, le=10.0)
    votes: int = Field(..., ge=0)
    meta_score: Optional[float] = Field(None, ge=0.0, le=100.0)
    gross: Optional[float] = Field(None, ge=0)
    description: str
    price: float = Field(..., ge=0)

    model_config = {"from_attributes": True}

    @field_validator("year")
    @classmethod
    def validate_year(cls, value):
        current_year = datetime.now().year
        if value > current_year + 1:
            raise ValueError(f"The year cannot be greater than {current_year + 1}.")
        return value


class MovieDetailSchema(MovieBaseSchema):
    id: int
    uuid: UUID
    certification: CertificationSchema
    genres: List[GenreSchema]
    directors: List[DirectorSchema]
    stars: List[StarSchema]

    model_config = {
        "from_attributes": True,
        "json_schema_extra": {"examples": [movie_detail_schema_example]},
    }


class MovieCreateSchema(BaseModel):
    name: str = Field(..., max_length=255)
    year: int = Field(..., ge=1800)
    time: int = Field(..., gt=0, description="Duration in minutes")
    imdb: float = Field(..., ge=0.0, le=10.0)
    votes: int = Field(..., ge=0)
    meta_score: Optional[float] = Field(None, ge=0.0, le=100.0)
    gross: Optional[float] = Field(None, ge=0)
    description: str
    price: float = Field(..., ge=0)
    certification: str
    genres: List[str] = Field(default_factory=list)
    directors: List[str] = Field(default_factory=list)
    stars: List[str] = Field(default_factory=list)

    model_config = {
        "from_attributes": True,
        "json_schema_extra": {"examples": [movie_create_schema_example]},
    }

    @field_validator("year")
    @classmethod
    def validate_year(cls, value):
        current_year = datetime.now().year
        if value > current_year + 1:
            raise ValueError(f"The year cannot be greater than {current_year + 1}.")
        return value

    @field_validator("certification", mode="before")
    @classmethod
    def normalize_certification(cls, value: str) -> str:
        return value.strip().upper()

    @field_validator("genres", "directors", "stars", mode="before")
    @classmethod
    def normalize_list_fields(cls, value: List[str]) -> List[str]:
        return [item.strip().title() for item in value]


class MovieUpdateSchema(BaseModel):
    name: Optional[str] = Field(None, max_length=255)
    year: Optional[int] = Field(None, ge=1800)
    time: Optional[int] = Field(None, gt=0)
    imdb: Optional[float] = Field(None, ge=0.0, le=10.0)
    votes: Optional[int] = Field(None, ge=0)
    meta_score: Optional[float] = Field(None, ge=0.0, le=100.0)
    gross: Optional[float] = Field(None, ge=0)
    description: Optional[str] = None
    price: Optional[float] = Field(None, ge=0)

    model_config = {
        "from_attributes": True,
        "json_schema_extra": {"examples": [movie_update_schema_example]},
    }

    @field_validator("year")
    @classmethod
    def validate_year(cls, value):
        if value is None:
            return value
        current_year = datetime.now().year
        if value > current_year + 1:
            raise ValueError(f"The year cannot be greater than {current_year + 1}.")
        return value


class GenreCreateSchema(BaseModel):
    name: str = Field(..., max_length=255)

    @field_validator("name", mode="before")
    @classmethod
    def normalize_name(cls, value: str) -> str:
        return value.strip().title()


class GenreUpdateSchema(BaseModel):
    name: Optional[str] = Field(None, max_length=255)

    @field_validator("name", mode="before")
    @classmethod
    def normalize_name(cls, value: str) -> str:
        if value is None:
            return value
        return value.strip().title()


class StarCreateSchema(BaseModel):
    name: str = Field(..., max_length=255)

    @field_validator("name", mode="before")
    @classmethod
    def normalize_name(cls, value: str) -> str:
        return value.strip().title()


class StarUpdateSchema(BaseModel):
    name: Optional[str] = Field(None, max_length=255)

    @field_validator("name", mode="before")
    @classmethod
    def normalize_name(cls, value: str) -> str:
        if value is None:
            return value
        return value.strip().title()


class UserFavoriteSchema(BaseModel):
    movie: MovieDetailSchema

    model_config = {"from_attributes": True}


class UserFavoriteCreateSchema(BaseModel):
    movie_id: int


class CommentCreateSchema(BaseModel):
    content: str = Field(..., min_length=1, max_length=500)
    movie_id: int = Field(..., gt=0)


class CommentUpdateSchema(BaseModel):
    content: str = Field(..., min_length=1, max_length=500)


class CommentSchema(BaseModel):
    id: int
    content: str
    movie_id: int
    user_id: int

    model_config = {"from_attributes": True}


class LikeSchema(BaseModel):
    id: int
    user_id: int
    likeable_id: int
    likeable_type: str

    model_config = {"from_attributes": True}
