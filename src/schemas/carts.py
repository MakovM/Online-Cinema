from datetime import datetime
from pydantic import BaseModel
from typing import List


class MessageResponse(BaseModel):
    message: str

class GenreSchema(BaseModel):
    id: int
    name: str

    model_config = {
        "from_attributes": True
    }


class CartMovieSchema(BaseModel):
    name: str
    price: float
    genres: List[GenreSchema]
    year: int

    model_config = {
        "from_attributes": True
    }

class CartItemCreate(BaseModel):
    movie_id: int


class CartItemResponse(BaseModel):
    id: int
    movie: CartMovieSchema
    added_at: datetime

    model_config = {
        "from_attributes": True
    }


class CartResponse(BaseModel):
    id: int
    user_id: int
    items: List[CartItemResponse]
    total_price: float

    model_config = {
        "from_attributes": True
    }

