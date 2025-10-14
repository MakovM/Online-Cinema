from typing import Optional
from fastapi_filter.contrib.sqlalchemy import Filter
from sqlalchemy.util.langhelpers import NoneType
from database.models.movies import Movie, Genre, Star


class MovieFilter(Filter):
    """
    Supports filtering by:
    - name__ilike: Case-insensitive partial match on movie name
    - year: Exact year, or year range (year__gte, year__lte)
    - imdb: IMDb rating exact or range (imdb__gte, imdb__lte)
    - price: Price range (price__gte, price__lte)
    - time: Duration in minutes (time__gte, time__lte)
    - meta_score: Metascore range (meta_score__gte, meta_score__lte)
    - votes: Vote count range (votes__gte, votes__lte)
    - gross: Gross revenue range (gross__gte, gross__lte)
    - search: Full-text search across name and description
    - order_by: Sort by fields (default: -year, -imdb)
    """
    
    name__ilike: Optional[str] = None

    year: Optional[int] = None
    year__gte: Optional[int] = None
    year__lte: Optional[int] = None

    imdb: Optional[float] = None
    imdb__gte: Optional[float] = None
    imdb__lte: Optional[float] = None

    price__gte: Optional[float] = None
    price__lte: Optional[float] = None

    time__gte: Optional[int] = None
    time__lte: Optional[int] = None

    meta_score__gte: Optional[float] = None
    meta_score__lte: Optional[float] = None

    votes__gte: Optional[int] = None
    votes__lte: Optional[int] = None

    gross__gte: Optional[float] = None
    gross__lte: Optional[float] = None

    order_by: Optional[list[str]] = ["-year", "-imdb"]

    search: Optional[str | NoneType] = None
    
    class Constants(Filter.Constants):
        model = Movie
        ordering_field_name = "order_by"
        search_field_name = "search"
        search_model_fields = ["name", "description"]


class GenreFilter(Filter):
    name__ilike: Optional[str] = None

class StarFilter(Filter):
    name__ilike: Optional[str] = None
