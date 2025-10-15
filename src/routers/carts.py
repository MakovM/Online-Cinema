from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, delete
from sqlalchemy.orm import selectinload, joinedload

from database.models.carts import Cart, CartItem
from database.models.movies import Movie
from schemas.carts import CartResponse, CartItemResponse, CartItemCreate, MessageResponse
from database import get_db, UserGroupEnum, OrderItemModel, OrderModel
from security.dependencies import get_current_user

router = APIRouter(prefix="/cart")


@router.get("/", response_model=CartResponse)
async def get_cart(
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user),
):
    cart_stmt = select(Cart).where(Cart.user_id == current_user.id).options(
        joinedload(Cart.items)
        .joinedload(CartItem.movie)
        .joinedload(Movie.genres)
    )
    cart: Cart | None = await db.scalar(cart_stmt)

    if not cart:
        cart = Cart(user_id=current_user.id)
        db.add(cart)
        await db.commit()
        await db.refresh(cart)

        reload_stmt = select(Cart).where(Cart.id == cart.id).options(
            joinedload(Cart.items)
            .joinedload(CartItem.movie)
            .joinedload(Movie.genres)
        )
        cart = await db.scalar(reload_stmt)

    if cart is None:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve or create cart."
        )

    items_response = [
        CartItemResponse(
            id=item.id,
            movie=item.movie,
            added_at=item.added_at
        )
        for item in cart.items
    ]

    return CartResponse(
        id=cart.id,
        user_id=current_user.id,
        items=items_response,
        total_price=cart.total_price()
    )


@router.post("/{target_user_id}/", response_model=CartResponse)
async def get_target_cart(
    target_user_id: int,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user),
):
    if not current_user.has_group(UserGroupEnum.MODERATOR) and not current_user.has_group(UserGroupEnum.ADMIN):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied!"
        )

    cart_stmt = select(Cart).where(Cart.user_id == target_user_id).options(
        joinedload(Cart.items)
        .joinedload(CartItem.movie)
        .joinedload(Movie.genres)
    )
    cart: Cart | None = await db.scalar(cart_stmt)

    if not cart:
        cart = Cart(user_id=target_user_id)
        db.add(cart)
        await db.commit()
        await db.refresh(cart)

        reload_stmt = select(Cart).where(Cart.id == cart.id).options(
            joinedload(Cart.items)
            .joinedload(CartItem.movie)
            .joinedload(Movie.genres)
        )
        cart = await db.scalar(reload_stmt)

    if cart is None:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve or create cart."
        )

    items_response = [
        CartItemResponse(
            id=item.id,
            movie=item.movie,
            added_at=item.added_at
        )
        for item in cart.items
    ]

    return CartResponse(
        id=cart.id,
        user_id=target_user_id,
        items=items_response,
        total_price=cart.total_price()
    )

@router.post("/items/{item_id}/add/", response_model=MessageResponse, status_code=status.HTTP_201_CREATED)
async def add_item_to_cart(
    item_id: int,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user),
):
    cart = await db.scalar(select(Cart).where(Cart.user_id == current_user.id))

    if not cart:
        cart = Cart(user_id=current_user.id)
        db.add(cart)
        await db.commit()
        await db.refresh(cart)

    item_exists = await db.get(Movie, item_id)
    if not item_exists:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Item does not exist",
        )

    item_in_cart = await db.scalar(
        select(CartItem).where(
            CartItem.cart_id == cart.id,
            CartItem.movie_id == item_id,
        )
    )
    if item_in_cart:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Item already in your cart.",
        )

    item_purchased = await db.scalar(
        select(OrderItemModel).join(OrderModel).where(
            OrderModel.user_id == current_user.id,
            OrderItemModel.movie_id == item_id,
        )
    )
    if item_purchased:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="You have already purchased this item.",
        )

    cart_item = CartItem(cart_id=cart.id, movie_id=item_id)
    db.add(cart_item)
    await db.commit()

    item_name = getattr(item_exists, 'title', getattr(item_exists, 'name', 'Item'))
    return MessageResponse(message=f"Item '{item_name}' successfully added to cart.")


@router.delete("/items/{item_id}/delete/", response_model=MessageResponse)
async def delete_item_from_cart(
    item_id: int,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user),
):
    cart = await db.scalar(select(Cart).where(Cart.user_id == current_user.id))
    if not cart:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Cart does not exist.",
        )

    item = await db.scalar(
        select(CartItem).where(
            CartItem.id == item_id,
            CartItem.cart_id == cart.id,
        )
    )
    if not item:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Item not found in your cart.",
        )

    await db.delete(item)
    await db.commit()

    return MessageResponse(message="Item removed from your cart successfully.")

@router.delete("/clear/", response_model=MessageResponse)
async def cart_clear(
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user),
):
    cart = await db.scalar(select(Cart).where(Cart.user_id == current_user.id))

    if not cart:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Cart not found")

    await db.execute(delete(CartItem).where(CartItem.cart_id == cart.id))
    await db.commit()

    return MessageResponse(message="Your cart successfully cleared.")