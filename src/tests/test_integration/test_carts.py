import pytest
from sqlalchemy import select

from database import UserModel, Cart, CartItem, OrderModel, OrderItemModel
from main import app


@pytest.mark.asyncio
async def test_get_cart_creates_new_cart_if_none_exists(user, db_session, jwt_manager, client):
    access_token = jwt_manager.create_access_token({"user_id": user.id})

    response = await client.get(
        app.url_path_for("get_cart"),
        headers={"Authorization": f"Bearer {access_token}"},
    )

    assert response.status_code == 200
    data = response.json()
    assert data["user_id"] == user.id
    assert data["items"] == []
    assert "id" in data


@pytest.mark.asyncio
async def test_get_existing_cart_with_items(user, movie, db_session, jwt_manager, client):
    cart = Cart(user_id=user.id)
    db_session.add(cart)
    await db_session.commit()
    await db_session.refresh(cart)

    cart_item = CartItem(cart_id=cart.id, movie_id=movie.id)
    db_session.add(cart_item)
    await db_session.commit()

    access_token = jwt_manager.create_access_token({"user_id": user.id})

    response = await client.get(
        app.url_path_for("get_cart"),
        headers={"Authorization": f"Bearer {access_token}"},
    )

    assert response.status_code == 200
    cart_data = response.json()

    assert cart_data["user_id"] == user.id
    assert len(cart_data["items"]) == 1, "Should return one cart item."
    assert cart_data["total_price"] == 228.0, "Total price should match the movie price."

    item_response = cart_data["items"][0]
    assert item_response["id"] == cart_item.id
    assert item_response["movie"]["name"] == "test"
    assert item_response["movie"]["price"] == 228.0


@pytest.mark.asyncio
async def test_get_cart_requires_authentication(client):
    response = await client.get(
        app.url_path_for("get_cart"),
    )
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_user_cannot_view_another_users_cart(
    user, movie, db_session, jwt_manager, client, seed_user_groups
):
    another_user = UserModel.create(
        email="test@mate.com", raw_password="TestPassword123!", group_id=1
    )
    another_user.is_active = True
    db_session.add(another_user)
    await db_session.flush()

    cart = Cart(user_id=another_user.id)
    db_session.add(cart)
    await db_session.flush()

    cart_item = CartItem(cart_id=cart.id, movie_id=movie.id)
    db_session.add(cart_item)
    await db_session.commit()

    access_token = jwt_manager.create_access_token({"user_id": user.id})
    headers = {"Authorization": f"Bearer {access_token}"}
    cart_url = app.url_path_for("get_target_cart", target_user_id=another_user.id)
    response = await client.post(cart_url, headers=headers)
    assert response.status_code in [
        401,
        403,
    ], f"Expected 401 or 403 for unauthorized access, got {response.status_code}. Details: {response.text}"


@pytest.mark.asyncio
async def test_moderator_can_view_another_users_cart(
    user, moderator, movie, db_session, jwt_manager, client, seed_user_groups
):
    cart = Cart(user_id=user.id)
    db_session.add(cart)
    await db_session.flush()

    cart_item = CartItem(cart_id=cart.id, movie_id=movie.id)
    db_session.add(cart_item)
    await db_session.commit()

    access_token = jwt_manager.create_access_token({"user_id": moderator.id})
    headers = {"Authorization": f"Bearer {access_token}"}
    cart_url = app.url_path_for("get_target_cart", target_user_id=user.id)
    response = await client.post(cart_url, headers=headers)
    assert response.status_code == 200
    cart_data = response.json()

    assert cart_data["user_id"] == user.id
    assert len(cart_data["items"]) == 1, "Should return one cart item."
    assert cart_data["total_price"] == 228.0, "Total price should match the movie price."

    item_response = cart_data["items"][0]
    assert item_response["id"] == cart_item.id
    assert item_response["movie"]["name"] == "test"
    assert item_response["movie"]["price"] == 228.0


@pytest.mark.asyncio
async def test_add_item_to_cart_success(
    user, movie, client, db_session, jwt_manager, seed_user_groups, seed_database
):
    access_token = jwt_manager.create_access_token({"user_id": user.id})

    response = await client.post(
        app.url_path_for("add_item_to_cart", item_id=movie.id),
        headers={"Authorization": f"Bearer {access_token}"},
    )

    assert response.status_code == 201
    assert response.json()["message"] == f"Item '{movie.name}' successfully added to cart."

    cart_item = await db_session.scalar(
        select(CartItem).join(Cart).where(Cart.user_id == user.id, CartItem.movie_id == movie.id)
    )
    assert cart_item is not None


@pytest.mark.asyncio
async def test_add_item_creates_cart_if_not_exists(
    user,
    movie,
    client,
    db_session,
    jwt_manager,
    seed_user_groups,
    seed_database,
):
    access_token = jwt_manager.create_access_token({"user_id": user.id})

    response = await client.post(
        app.url_path_for("add_item_to_cart", item_id=movie.id),
        headers={"Authorization": f"Bearer {access_token}"},
    )

    assert response.status_code == 201

    cart = await db_session.scalar(select(Cart).where(Cart.user_id == user.id))
    assert cart is not None


@pytest.mark.asyncio
async def test_add_nonexistent_item_returns_404(
    user,
    client,
    db_session,
    jwt_manager,
    seed_user_groups,
):
    access_token = jwt_manager.create_access_token({"user_id": user.id})

    response = await client.post(
        app.url_path_for("add_item_to_cart", item_id=-2),
        headers={"Authorization": f"Bearer {access_token}"},
    )

    assert response.status_code == 404
    assert response.json()["detail"] == "Item does not exist"


@pytest.mark.asyncio
async def test_add_duplicate_item_returns_400(
    user,
    movie,
    client,
    db_session,
    jwt_manager,
    seed_user_groups,
    seed_database,
):
    cart = Cart(user_id=user.id)
    db_session.add(cart)
    await db_session.commit()
    await db_session.refresh(cart)

    cart_item = CartItem(cart_id=cart.id, movie_id=movie.id)
    db_session.add(cart_item)
    await db_session.commit()

    access_token = jwt_manager.create_access_token({"user_id": user.id})

    response = await client.post(
        app.url_path_for("add_item_to_cart", item_id=movie.id),
        headers={"Authorization": f"Bearer {access_token}"},
    )

    assert response.status_code == 400
    assert response.json()["detail"] == "Item already in your cart."


@pytest.mark.asyncio
async def test_add_purchased_item_returns_400(
    user,
    movie,
    client,
    db_session,
    jwt_manager,
    seed_user_groups,
    seed_database,
):
    order = OrderModel(user_id=user.id, status="paid", total_amount=1.0)
    db_session.add(order)
    await db_session.commit()
    await db_session.refresh(order)

    order_item = OrderItemModel(order_id=order.id, movie_id=movie.id, price_at_order=1.0)
    db_session.add(order_item)
    await db_session.commit()

    access_token = jwt_manager.create_access_token({"user_id": user.id})

    response = await client.post(
        app.url_path_for("add_item_to_cart", item_id=movie.id),
        headers={"Authorization": f"Bearer {access_token}"},
    )

    assert response.status_code == 400
    assert response.json()["detail"] == "You have already purchased this item."


async def test_remove_item_from_cart_success(
    user,
    movie,
    client,
    db_session,
    jwt_manager,
    seed_user_groups,
    seed_database,
):
    cart = Cart(user_id=user.id)
    db_session.add(cart)
    await db_session.commit()
    await db_session.refresh(cart)

    cart_item = CartItem(cart_id=cart.id, movie_id=movie.id)
    db_session.add(cart_item)
    await db_session.commit()
    await db_session.refresh(cart_item)

    access_token = jwt_manager.create_access_token({"user_id": user.id})

    response = await client.delete(
        app.url_path_for("delete_item_from_cart", item_id=cart_item.id),
        headers={"Authorization": f"Bearer {access_token}"},
    )

    assert response.status_code == 200
    assert response.json()["message"] == "Item removed from your cart successfully."


async def test_remove_nonexistent_item_returns_404(
    user,
    client,
    db_session,
    jwt_manager,
    seed_user_groups,
):
    cart = Cart(user_id=user.id)
    db_session.add(cart)
    await db_session.commit()

    access_token = jwt_manager.create_access_token({"user_id": user.id})

    response = await client.delete(
        app.url_path_for("delete_item_from_cart", item_id=-1),
        headers={"Authorization": f"Bearer {access_token}"},
    )

    assert response.status_code == 404
    assert response.json()["detail"] == "Item not found in your cart."


async def test_clear_cart_success(
    user,
    movie,
    client,
    db_session,
    jwt_manager,
    seed_user_groups,
    seed_database,
):
    cart = Cart(user_id=user.id)
    db_session.add(cart)
    await db_session.commit()
    await db_session.refresh(cart)

    cart_item = CartItem(cart_id=cart.id, movie_id=movie.id)
    db_session.add(cart_item)
    await db_session.commit()

    access_token = jwt_manager.create_access_token({"user_id": user.id})

    response = await client.delete(
        app.url_path_for("cart_clear"),
        headers={"Authorization": f"Bearer {access_token}"},
    )

    assert response.status_code == 200

    remaining_items = await db_session.scalars(select(CartItem).where(CartItem.cart_id == cart.id))
    assert len(list(remaining_items)) == 0


async def test_clear_empty_cart_success(
    user,
    client,
    db_session,
    jwt_manager,
    seed_user_groups,
):
    cart = Cart(user_id=user.id)
    db_session.add(cart)
    await db_session.commit()

    access_token = jwt_manager.create_access_token({"user_id": user.id})

    response = await client.delete(
        app.url_path_for("cart_clear"),
        headers={"Authorization": f"Bearer {access_token}"},
    )

    assert response.status_code == 200