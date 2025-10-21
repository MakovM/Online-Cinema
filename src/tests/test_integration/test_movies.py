import pytest

from database.models.movies import UserFavorite, Comment


@pytest.mark.asyncio
async def test_create_movie(client, moderator_headers, seed_user_groups):
    movie_data = {
        "name": "Inception",
        "year": 2010,
        "time": 148,
        "imdb": 8.8,
        "votes": 2000000,
        "meta_score": 74.0,
        "gross": 829.9,
        "description": "A thief who steals corporate secrets.",
        "price": 12.99,
        "certification": "PG-13",
        "genres": ["Action", "Sci-Fi"],
        "directors": ["Christopher Nolan"],
        "stars": ["Leonardo DiCaprio"]
    }

    response = await client.post(
        "/api/v1/movies/", json=movie_data, headers=moderator_headers
    )
    assert response.status_code == 201
    assert response.json()["name"] == "Inception"


@pytest.mark.asyncio
async def test_update_movie(movie, client, moderator_headers, seed_user_groups):
    response = await client.patch(
        f"/api/v1/movies/{movie.id}/",
        json={"name": "Updated Movie", "imdb": 9.0},
        headers=moderator_headers
    )
    assert response.status_code == 200
    assert response.json()["name"] == "Updated Movie"
    assert response.json()["imdb"] == 9.0


@pytest.mark.asyncio
async def test_delete_movie(movie, client, moderator_headers, seed_user_groups):
    response = await client.delete(
        f"/api/v1/movies/{movie.id}/", headers=moderator_headers
    )
    assert response.status_code == 204


@pytest.mark.asyncio
async def test_create_comment(movie, client, user_headers):
    response = await client.post(
        "/api/v1/comments/",
        json={"content": "This is an amazing movie!", "movie_id": movie.id},
        headers=user_headers
    )
    assert response.status_code == 201
    assert response.json()["content"] == "This is an amazing movie!"
    assert response.json()["movie_id"] == movie.id


@pytest.mark.asyncio
async def test_update_comment(user, movie, db_session, client, user_headers):
    comment = Comment(content="Old comment", movie_id=movie.id, user_id=user.id)
    db_session.add(comment)
    await db_session.commit()
    await db_session.refresh(comment)

    response = await client.patch(
        f"/api/v1/comments/{comment.id}/",
        json={"content": "Updated comment"},
        headers=user_headers
    )
    assert response.status_code == 200
    assert response.json()["content"] == "Updated comment"


@pytest.mark.asyncio
async def test_delete_comment(user, movie, db_session, client, user_headers):
    comment = Comment(content="Comment to delete", movie_id=movie.id, user_id=user.id)
    db_session.add(comment)
    await db_session.commit()
    await db_session.refresh(comment)

    response = await client.delete(
        f"/api/v1/comments/{comment.id}/", headers=user_headers
    )
    assert response.status_code == 204


@pytest.mark.asyncio
async def test_toggle_comment_like(user, movie, db_session, client, user_headers):
    comment = Comment(content="Great comment", movie_id=movie.id, user_id=user.id)
    db_session.add(comment)
    await db_session.commit()
    await db_session.refresh(comment)

    response = await client.post(
        f"/api/v1/comments/{comment.id}/toggle-like/", headers=user_headers
    )
    assert response.status_code == 200
    assert response.json()["liked"] is True

    response = await client.post(
        f"/api/v1/comments/{comment.id}/toggle-like/", headers=user_headers
    )
    assert response.status_code == 200
    assert response.json()["liked"] is False


@pytest.mark.asyncio
async def test_add_to_favorites(movie, client, user_headers):
    response = await client.post(
        "/api/v1/movies/favorites/",
        json={"movie_id": movie.id},
        headers=user_headers
    )
    assert response.status_code == 201
    assert response.json()["message"] == "Movie added to favorites"


@pytest.mark.asyncio
async def test_remove_from_favorites(user, movie, db_session, client, user_headers):
    favorite = UserFavorite(user_id=user.id, movie_id=movie.id)
    db_session.add(favorite)
    await db_session.commit()

    response = await client.delete(
        f"/api/v1/movies/favorites/{movie.id}/", headers=user_headers
    )
    assert response.status_code == 204


@pytest.mark.asyncio
async def test_toggle_movie_like(movie, client, user_headers):
    response = await client.post(
        f"/api/v1/movies/{movie.id}/toggle-like/", headers=user_headers
    )
    assert response.status_code == 200
    assert response.json()["liked"] is True

    response = await client.post(
        f"/api/v1/movies/{movie.id}/toggle-like/", headers=user_headers
    )
    assert response.status_code == 200
    assert response.json()["liked"] is False
