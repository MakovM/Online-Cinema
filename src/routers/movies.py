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
    UserFavorite,
    Like,
    movie_genres,
)
from schemas.movies import (
    MovieDetailSchema,
    MovieCreateSchema,
    MovieUpdateSchema,
    GenreSchema,
    GenreWithCountSchema,
    GenreCreateSchema,
    GenreUpdateSchema,
    StarSchema,
    StarCreateSchema,
    StarUpdateSchema,
    UserFavoriteCreateSchema,
)
from filters import MovieFilter, GenreFilter, StarFilter
from security.dependencies import AdminUser, CurrentUser, ModerAdminUser

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
            func.count(movie_genres.c.movie_id).label("movie_count"),
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
    genre_data: GenreCreateSchema,
    db: AsyncSession = Depends(get_db),
    allowed_user: ModerAdminUser = None,
):
    result = await db.execute(select(Genre).where(Genre.name == genre_data.name))
    if result.scalars().first():
        raise HTTPException(status_code=400, detail="Genre already exists")

    genre = Genre(name=genre_data.name)
    db.add(genre)
    await db.commit()
    await db.refresh(genre)
    return GenreSchema.model_validate(genre)


@router.get("/genres/{genre_id}/", response_model=Page[MovieDetailSchema])
async def get_genre(
    genre_id: int,
    movie_filter: MovieFilter = FilterDepends(MovieFilter),
    db: AsyncSession = Depends(get_db),
):
    genre_result = await db.execute(select(Genre).where(Genre.id == genre_id))
    genre = genre_result.scalars().first()

    if not genre:
        raise HTTPException(status_code=404, detail="Genre not found")

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


@router.patch("/genres/{genre_id}/", response_model=GenreSchema)
async def update_genre(
    genre_id: int,
    genre_data: GenreUpdateSchema,
    db: AsyncSession = Depends(get_db),
    allowed_user: ModerAdminUser = None,
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
async def delete_genre(
    genre_id: int,
    db: AsyncSession = Depends(get_db),
    allowed_user: ModerAdminUser = None,
):
    result = await db.execute(select(Genre).where(Genre.id == genre_id))
    genre = result.scalars().first()

    if not genre:
        raise HTTPException(status_code=404, detail="Genre not found")

    await db.delete(genre)
    await db.commit()


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
async def create_star(
    star_data: StarCreateSchema,
    db: AsyncSession = Depends(get_db),
    allowed_user: ModerAdminUser = None,
):
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
    star_id: int,
    star_data: StarUpdateSchema,
    db: AsyncSession = Depends(get_db),
    allowed_user: ModerAdminUser = None,
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
async def delete_star(
    star_id: int,
    db: AsyncSession = Depends(get_db),
    allowed_user: ModerAdminUser = None,
):
    result = await db.execute(select(Star).where(Star.id == star_id))
    star = result.scalars().first()

    if not star:
        raise HTTPException(status_code=404, detail="Star not found")

    await db.delete(star)
    await db.commit()


@router.get("/favorites/", response_model=Page[MovieDetailSchema])
async def get_user_favorites(
    movie_filter: MovieFilter = FilterDepends(MovieFilter),
    db: AsyncSession = Depends(get_db),
    current_user: CurrentUser = None,
):
    stmt = (
        select(Movie)
        .join(UserFavorite, Movie.id == UserFavorite.movie_id)
        .where(UserFavorite.user_id == current_user.id)
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

    return paginate([MovieDetailSchema.model_validate(movie) for movie in movies])


@router.post("/favorites/", status_code=201)
async def add_to_favorites(
    favorite_data: UserFavoriteCreateSchema,
    db: AsyncSession = Depends(get_db),
    current_user: CurrentUser = None,
):
    movie_stmt = select(Movie).where(Movie.id == favorite_data.movie_id)
    movie_result = await db.execute(movie_stmt)
    movie = movie_result.scalars().first()

    if not movie:
        raise HTTPException(status_code=404, detail="Movie not found")

    existing_favorite_stmt = select(UserFavorite).where(
        UserFavorite.user_id == current_user.id, UserFavorite.movie_id == favorite_data.movie_id
    )
    existing_favorite_result = await db.execute(existing_favorite_stmt)
    existing_favorite = existing_favorite_result.scalars().first()

    if existing_favorite:
        raise HTTPException(status_code=400, detail="Movie is already in favorites")

    favorite = UserFavorite(user_id=current_user.id, movie_id=favorite_data.movie_id)
    db.add(favorite)
    await db.commit()

    return {"message": "Movie added to favorites"}


@router.delete("/favorites/{movie_id}/", status_code=204)
async def remove_from_favorites(
    movie_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: CurrentUser = None,
):
    favorite_stmt = select(UserFavorite).where(
        UserFavorite.user_id == current_user.id, UserFavorite.movie_id == movie_id
    )
    favorite_result = await db.execute(favorite_stmt)
    favorite = favorite_result.scalars().first()

    if not favorite:
        raise HTTPException(status_code=404, detail="Movie not found in favorites")

    await db.delete(favorite)
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
    movie_data: MovieCreateSchema,
    db: AsyncSession = Depends(get_db),
    allowed_user: ModerAdminUser = None,
):
    try:
        cert_stmt = select(Certification).where(Certification.name == movie_data.certification)
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
    movie_id: int,
    movie_data: MovieUpdateSchema,
    db: AsyncSession = Depends(get_db),
    allowed_user: ModerAdminUser = None,
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
async def delete_movie(
    movie_id: int,
    db: AsyncSession = Depends(get_db),
    allowed_user: ModerAdminUser = None,
):
    stmt = select(Movie).where(Movie.id == movie_id)
    result = await db.execute(stmt)
    movie = result.scalars().first()

    if not movie:
        raise HTTPException(status_code=404, detail="Movie not found")

    await db.delete(movie)
    await db.commit()

    return {"detail": "Movie deleted successfully."}


@router.post("/{movie_id}/toggle-like/", status_code=200)
async def toggle_movie_like(
    movie_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: CurrentUser = None,
):
    movie = await db.get(Movie, movie_id)
    if not movie:
        raise HTTPException(status_code=404, detail="Movie not found")

    stmt = select(Like).where(
        Like.user_id == current_user.id, Like.likeable_id == movie_id, Like.likeable_type == "movie"
    )
    result = await db.execute(stmt)
    existing_like = result.scalars().first()

    if existing_like:
        await db.delete(existing_like)
        await db.commit()
        return {"detail": "Movie unliked successfully", "liked": False}
    else:
        like = Like(user_id=current_user.id, likeable_id=movie_id, likeable_type="movie")
        db.add(like)
        await db.commit()
        await db.refresh(like)
        return {"detail": "Movie liked successfully", "liked": True}
