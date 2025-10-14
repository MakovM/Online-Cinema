from fastapi import APIRouter, Depends, HTTPException
from fastapi_filter import FilterDepends
from fastapi_pagination import Page, paginate
from sqlalchemy import select, func
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload

from database import (
    get_db,
)
from database.models.movies import (
    Movie,
    Genre,
    Star,
    Director,
    Certification,
    movie_genres,
)
from schemas.movies import (
    MovieDetailSchema,
    MovieListItemSchema,
    MovieCreateSchema,
    MovieUpdateSchema,
    GenreSchema,
    GenreWithCountSchema,
    GenreDetailSchema,
    GenreCreateSchema,
    GenreUpdateSchema,
    StarSchema,
    StarCreateSchema,
    StarUpdateSchema,
)
from filters import MovieFilter, GenreFilter, StarFilter

router = APIRouter()


@router.get("/genres/", response_model=Page[GenreWithCountSchema])
async def get_genres(
    genre_filter: GenreFilter = FilterDepends(GenreFilter),
    db: AsyncSession = Depends(get_db),
):
    stmt = genre_filter.filter(
        select(
            Genre.id,
            Genre.name,
            func.count(movie_genres.c.movie_id).label("movie_count")
        )
        .outerjoin(movie_genres, Genre.id == movie_genres.c.genre_id)
        .group_by(Genre.id, Genre.name)
        .order_by(Genre.name)
    )
    result = await db.execute(stmt)
    genres = [
        GenreWithCountSchema(id=row.id, name=row.name, movie_count=row.movie_count)
        for row in result.all()
    ]
    return paginate(genres)


@router.post("/genres/", response_model=GenreSchema, status_code=201)
async def create_genre(
    genre_data: GenreCreateSchema, db: AsyncSession = Depends(get_db)
):
    result = await db.execute(select(Genre).where(Genre.name == genre_data.name))
    if result.scalars().first():
        raise HTTPException(status_code=400, detail="Genre already exists")

    genre = Genre(name=genre_data.name)
    db.add(genre)
    await db.commit()
    await db.refresh(genre)
    return GenreSchema.model_validate(genre)


@router.get("/genres/{genre_id}/", response_model=GenreDetailSchema)
async def get_genre(genre_id: int, db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(Genre)
        .where(Genre.id == genre_id)
        .options(joinedload(Genre.movies))
    )
    genre = result.scalars().first()

    if not genre:
        raise HTTPException(status_code=404, detail="Genre not found")

    return GenreDetailSchema(
        id=genre.id,
        name=genre.name,
        movies=[MovieListItemSchema.model_validate(m) for m in genre.movies]
    )


@router.patch("/genres/{genre_id}/", response_model=GenreSchema)
async def update_genre(
    genre_id: int, genre_data: GenreUpdateSchema, db: AsyncSession = Depends(get_db)
):
    result = await db.execute(select(Genre).where(Genre.id == genre_id))
    genre = result.scalars().first()

    if not genre:
        raise HTTPException(status_code=404, detail="Genre not found")

    for field, value in genre_data.model_dump(exclude_unset=True).items():
        setattr(genre, field, value)

    await db.commit()
    await db.refresh(genre)
    return GenreSchema.model_validate(genre)


@router.delete("/genres/{genre_id}/", status_code=204)
async def delete_genre(genre_id: int, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Genre).where(Genre.id == genre_id))
    genre = result.scalars().first()

    if not genre:
        raise HTTPException(status_code=404, detail="Genre not found")

    await db.delete(genre)
    await db.commit()


@router.get("/genres/{genre_id}/movies/", response_model=Page[MovieDetailSchema])
async def get_movies_by_genre(
    genre_id: int,
    movie_filter: MovieFilter = FilterDepends(MovieFilter),
    db: AsyncSession = Depends(get_db),
):
    stmt = (
        select(Movie)
        .join(movie_genres, Movie.id == movie_genres.c.movie_id)
        .where(movie_genres.c.genre_id == genre_id)
        .options(
            joinedload(Movie.certification),
            joinedload(Movie.genres),
            joinedload(Movie.directors),
            joinedload(Movie.stars),
        )
    )
    stmt = movie_filter.filter(stmt)
    stmt = movie_filter.sort(stmt)
    
    result = await db.execute(stmt)
    movies = result.scalars().unique().all()
    return paginate([MovieDetailSchema.model_validate(m) for m in movies])


@router.get("/stars/", response_model=Page[StarSchema])
async def get_stars(
    star_filter: StarFilter = FilterDepends(StarFilter),
    db: AsyncSession = Depends(get_db),
):
    stmt = star_filter.filter(select(Star).order_by(Star.name))
    result = await db.execute(stmt)
    stars = result.scalars().all()
    return paginate([StarSchema.model_validate(star) for star in stars])


@router.post("/stars/", response_model=StarSchema, status_code=201)
async def create_star(star_data: StarCreateSchema, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Star).where(Star.name == star_data.name))
    if result.scalars().first():
        raise HTTPException(status_code=400, detail="Star already exists")

    star = Star(name=star_data.name)
    db.add(star)
    await db.commit()
    await db.refresh(star)
    return StarSchema.model_validate(star)


@router.get("/stars/{star_id}/", response_model=StarSchema)
async def get_star(star_id: int, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Star).where(Star.id == star_id))
    star = result.scalars().first()

    if not star:
        raise HTTPException(status_code=404, detail="Star not found")

    return StarSchema.model_validate(star)


@router.patch("/stars/{star_id}/", response_model=StarSchema)
async def update_star(
    star_id: int, star_data: StarUpdateSchema, db: AsyncSession = Depends(get_db)
):
    result = await db.execute(select(Star).where(Star.id == star_id))
    star = result.scalars().first()

    if not star:
        raise HTTPException(status_code=404, detail="Star not found")

    for field, value in star_data.model_dump(exclude_unset=True).items():
        setattr(star, field, value)

    await db.commit()
    await db.refresh(star)
    return StarSchema.model_validate(star)


@router.delete("/stars/{star_id}/", status_code=204)
async def delete_star(star_id: int, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Star).where(Star.id == star_id))
    star = result.scalars().first()

    if not star:
        raise HTTPException(status_code=404, detail="Star not found")

    await db.delete(star)
    await db.commit()


@router.get("/", response_model=Page[MovieDetailSchema])
async def get_movies(
    movie_filter: MovieFilter = FilterDepends(MovieFilter),
    db: AsyncSession = Depends(get_db),
):
    stmt = select(Movie).options(
        joinedload(Movie.certification),
        joinedload(Movie.genres),
        joinedload(Movie.directors),
        joinedload(Movie.stars),
    )
    stmt = movie_filter.filter(stmt)
    stmt = movie_filter.sort(stmt)
    result = await db.execute(stmt)
    movies = result.scalars().unique().all()
    movies_schemas = [MovieDetailSchema.model_validate(movie) for movie in movies]
    return paginate(movies_schemas)


@router.post("/", response_model=MovieDetailSchema, status_code=201)
async def create_movie(
    movie_data: MovieCreateSchema, db: AsyncSession = Depends(get_db)
):
    try:
        cert_stmt = select(Certification).where(
            Certification.name == movie_data.certification
        )
        cert_result = await db.execute(cert_stmt)
        certification = cert_result.scalars().first()

        if not certification:
            certification = Certification(name=movie_data.certification)
            db.add(certification)
            await db.flush()

        genres = []
        for genre_name in movie_data.genres:
            genre_stmt = select(Genre).where(Genre.name == genre_name)
            genre_result = await db.execute(genre_stmt)
            genre = genre_result.scalars().first()

            if not genre:
                genre = Genre(name=genre_name)
                db.add(genre)
                await db.flush()
            genres.append(genre)

        directors = []
        for director_name in movie_data.directors:
            director_stmt = select(Director).where(Director.name == director_name)
            director_result = await db.execute(director_stmt)
            director = director_result.scalars().first()

            if not director:
                director = Director(name=director_name)
                db.add(director)
                await db.flush()
            directors.append(director)

        stars = []
        for star_name in movie_data.stars:
            star_stmt = select(Star).where(Star.name == star_name)
            star_result = await db.execute(star_stmt)
            star = star_result.scalars().first()

            if not star:
                star = Star(name=star_name)
                db.add(star)
                await db.flush()
            stars.append(star)

        movie = Movie(
            name=movie_data.name,
            year=movie_data.year,
            time=movie_data.time,
            imdb=movie_data.imdb,
            votes=movie_data.votes,
            meta_score=movie_data.meta_score,
            gross=movie_data.gross,
            description=movie_data.description,
            price=movie_data.price,
            certification=certification,
            genres=genres,
            directors=directors,
            stars=stars,
        )

        db.add(movie)
        await db.commit()
        await db.refresh(movie, ["certification", "genres", "directors", "stars"])

        return MovieDetailSchema.model_validate(movie)

    except IntegrityError:
        await db.rollback()
        raise HTTPException(status_code=400, detail="Invalid input data.")


@router.get("/{movie_id}/", response_model=MovieDetailSchema)
async def get_movie(movie_id: int, db: AsyncSession = Depends(get_db)):
    stmt = (
        select(Movie)
        .options(
            joinedload(Movie.certification),
            joinedload(Movie.genres),
            joinedload(Movie.directors),
            joinedload(Movie.stars),
        )
        .where(Movie.id == movie_id)
    )
    result = await db.execute(stmt)
    movie = result.scalars().first()

    if not movie:
        raise HTTPException(status_code=404, detail="Movie not found")

    return MovieDetailSchema.model_validate(movie)


@router.patch("/{movie_id}/", response_model=MovieDetailSchema)
async def update_movie(
    movie_id: int, movie_data: MovieUpdateSchema, db: AsyncSession = Depends(get_db)
):
    stmt = select(Movie).where(Movie.id == movie_id)
    result = await db.execute(stmt)
    movie = result.scalars().first()

    if not movie:
        raise HTTPException(status_code=404, detail="Movie not found")

    for field, value in movie_data.model_dump(exclude_unset=True).items():
        setattr(movie, field, value)

    try:
        await db.commit()
        await db.refresh(movie, ["certification", "genres", "directors", "stars"])
    except IntegrityError:
        await db.rollback()
        raise HTTPException(status_code=400, detail="Invalid input data.")

    return MovieDetailSchema.model_validate(movie)


@router.delete("/{movie_id}/", status_code=204)
async def delete_movie(movie_id: int, db: AsyncSession = Depends(get_db)):
    stmt = select(Movie).where(Movie.id == movie_id)
    result = await db.execute(stmt)
    movie = result.scalars().first()

    if not movie:
        raise HTTPException(status_code=404, detail="Movie not found")

    await db.delete(movie)
    await db.commit()

    return {"detail": "Movie deleted successfully."}
