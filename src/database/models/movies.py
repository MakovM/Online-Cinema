import uuid as uuid_pkg
from typing import Optional, TYPE_CHECKING

if TYPE_CHECKING:
    from database.models.accounts import UserModel

from sqlalchemy import (
    String,
    Float,
    Text,
    DECIMAL,
    UniqueConstraint,
    ForeignKey,
    Table,
    Column,
    Integer,
)
from sqlalchemy.dialects.postgresql import UUID, ENUM
from sqlalchemy.orm import mapped_column, Mapped, relationship

from database.models.base import Base


# Association Tables
movie_genres = Table(
    "movie_genres",
    Base.metadata,
    Column("movie_id", ForeignKey("movies.id", ondelete="CASCADE"), primary_key=True),
    Column("genre_id", ForeignKey("genres.id", ondelete="CASCADE"), primary_key=True),
)

movie_stars = Table(
    "movie_stars",
    Base.metadata,
    Column("movie_id", ForeignKey("movies.id", ondelete="CASCADE"), primary_key=True),
    Column("star_id", ForeignKey("stars.id", ondelete="CASCADE"), primary_key=True),
)

movie_directors = Table(
    "movie_directors",
    Base.metadata,
    Column("movie_id", ForeignKey("movies.id", ondelete="CASCADE"), primary_key=True),
    Column("director_id", ForeignKey("directors.id", ondelete="CASCADE"), primary_key=True),
)


class Genre(Base):
    """Represents a movie genre (e.g., Action, Drama, Comedy)."""

    __tablename__ = "genres"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(255), unique=True, nullable=False)

    movies: Mapped[list["Movie"]] = relationship(
        "Movie", secondary=movie_genres, back_populates="genres"
    )

    def __repr__(self):
        return f"<Genre(id={self.id}, name='{self.name}')>"


class Star(Base):
    """Represents an actor or actress starring in a movie."""

    __tablename__ = "stars"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(255), unique=True, nullable=False)

    movies: Mapped[list["Movie"]] = relationship(
        "Movie", secondary=movie_stars, back_populates="stars"
    )

    def __repr__(self):
        return f"<Star(id={self.id}, name='{self.name}')>"


class Director(Base):
    """Represents a movie director."""

    __tablename__ = "directors"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(255), unique=True, nullable=False)

    movies: Mapped[list["Movie"]] = relationship(
        "Movie", secondary=movie_directors, back_populates="directors"
    )

    def __repr__(self):
        return f"<Director(id={self.id}, name='{self.name}')>"


class Certification(Base):
    """Represents the rating or certification of a movie (e.g., PG-13, R)."""

    __tablename__ = "certifications"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(50), unique=True, nullable=False)

    movies: Mapped[list["Movie"]] = relationship("Movie", back_populates="certification")

    def __repr__(self):
        return f"<Certification(id={self.id}, name='{self.name}')>"


class Movie(Base):
    """Represents a movie's main data."""

    __tablename__ = "movies"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    uuid: Mapped[uuid_pkg.UUID] = mapped_column(
        UUID(as_uuid=True), unique=True, nullable=False, default=uuid_pkg.uuid4
    )
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    year: Mapped[int] = mapped_column(Integer, nullable=False)
    time: Mapped[int] = mapped_column(Integer, nullable=False)  # duration in minutes
    imdb: Mapped[float] = mapped_column(Float, nullable=False)  # IMDb rating
    votes: Mapped[int] = mapped_column(Integer, nullable=False)  # number of votes
    meta_score: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    gross: Mapped[Optional[float]] = mapped_column(Float, nullable=True)  # gross revenue
    description: Mapped[str] = mapped_column(Text, nullable=False)
    price: Mapped[float] = mapped_column(DECIMAL(10, 2), nullable=False)

    certification_id: Mapped[int] = mapped_column(ForeignKey("certifications.id"), nullable=False)

    # Relationships
    certification: Mapped["Certification"] = relationship("Certification", back_populates="movies")

    genres: Mapped[list["Genre"]] = relationship(
        "Genre", secondary=movie_genres, back_populates="movies"
    )

    directors: Mapped[list["Director"]] = relationship(
        "Director", secondary=movie_directors, back_populates="movies"
    )

    stars: Mapped[list["Star"]] = relationship(
        "Star", secondary=movie_stars, back_populates="movies"
    )

    favorited_by: Mapped[list["UserFavorite"]] = relationship(
        "UserFavorite", back_populates="movie"
    )

    __table_args__ = (UniqueConstraint("name", "year", "time", name="uq_movie_name_year_time"),)

    @classmethod
    def default_order_by(cls):
        return [cls.id.desc()]

    def __repr__(self):
        return f"<Movie(id={self.id}, name='{self.name}', year={self.year})>"


class UserFavorite(Base):
    __tablename__ = "user_favorites"

    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), primary_key=True
    )
    movie_id: Mapped[int] = mapped_column(
        ForeignKey("movies.id", ondelete="CASCADE"), primary_key=True
    )

    user: Mapped["UserModel"] = relationship("UserModel", back_populates="favorites")
    movie: Mapped["Movie"] = relationship("Movie", back_populates="favorited_by")

    def __repr__(self):
        return f"<UserFavorite(user_id={self.user_id}, movie_id={self.movie_id})>"


class Comment(Base):
    """Represents a user comment on a movie."""

    __tablename__ = "comments"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    content: Mapped[str] = mapped_column(Text, nullable=False)
    movie_id: Mapped[int] = mapped_column(
        ForeignKey("movies.id", ondelete="CASCADE"), nullable=False
    )
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), nullable=False)

    def __repr__(self):
        return f"<Comment(id={self.id}, movie_id={self.movie_id}, user_id={self.user_id})>"


class Like(Base):
    __tablename__ = "likes"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    likeable_id: Mapped[int] = mapped_column(Integer, nullable=False)
    likeable_type: Mapped[str] = mapped_column(
        ENUM("movie", "comment", name="likeable_types"), nullable=False
    )

    def __repr__(self):
        return (
            f"<Like(id={self.id}, user_id={self.user_id}, "
            f"likeable_id={self.likeable_id}, "
            f"likeable_type='{self.likeable_type}')>"
        )
