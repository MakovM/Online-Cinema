genre_schema_example = {"id": 1, "name": "Action"}

star_schema_example = {"id": 1, "name": "Tom Cruise"}

director_schema_example = {"id": 1, "name": "Christopher Nolan"}

certification_schema_example = {"id": 1, "name": "PG-13"}

movie_detail_schema_example = {
    "id": 1,
    "uuid": "550e8400-e29b-41d4-a716-446655440000",
    "name": "Inception",
    "year": 2010,
    "time": 148,
    "imdb": 8.8,
    "votes": 2000000,
    "meta_score": 74.0,
    "gross": 829895144.0,
    "description": "A thief who steals corporate secrets through the use of dream-sharing technology...",
    "price": 9.99,
    "certification": certification_schema_example,
    "genres": [genre_schema_example],
    "directors": [director_schema_example],
    "stars": [star_schema_example],
}

movie_create_schema_example = {
    "name": "Inception",
    "year": 2010,
    "time": 148,
    "imdb": 8.8,
    "votes": 2000000,
    "meta_score": 74.0,
    "gross": 829895144.0,
    "description": "A thief who steals corporate secrets through the use of dream-sharing technology...",
    "price": 9.99,
    "certification": "PG-13",
    "genres": ["Action", "Sci-Fi", "Thriller"],
    "directors": ["Christopher Nolan"],
    "stars": ["Leonardo DiCaprio", "Joseph Gordon-Levitt", "Elliot Page"],
}

movie_update_schema_example = {
    "name": "Inception (Updated)",
    "year": 2010,
    "price": 12.99,
    "description": "Updated description...",
}
