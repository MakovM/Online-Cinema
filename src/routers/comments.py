from fastapi import APIRouter, Depends, HTTPException
from fastapi_pagination import Page, paginate
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from database import get_db
from database.models.movies import Comment, Movie, Like
from schemas.movies import CommentCreateSchema, CommentUpdateSchema, CommentSchema
from security.dependencies import CurrentUser

router = APIRouter()


@router.post("/", response_model=CommentSchema, status_code=201)
async def create_comment(
    comment_data: CommentCreateSchema,
    db: AsyncSession = Depends(get_db),
    current_user: CurrentUser = None,
):
    movie = await db.get(Movie, comment_data.movie_id)
    if not movie:
        raise HTTPException(status_code=404, detail="Movie not found")

    comment = Comment(
        content=comment_data.content,
        movie_id=comment_data.movie_id,
        user_id=current_user.id,
    )

    db.add(comment)
    await db.commit()
    await db.refresh(comment)

    return CommentSchema.model_validate(comment)


@router.get("/movie/{movie_id}/", response_model=Page[CommentSchema])
async def get_movie_comments(
    movie_id: int,
    db: AsyncSession = Depends(get_db),
):
    movie = await db.get(Movie, movie_id)
    if not movie:
        raise HTTPException(status_code=404, detail="Movie not found")

    stmt = select(Comment).where(Comment.movie_id == movie_id)
    result = await db.execute(stmt)
    comments = result.scalars().all()

    return paginate([CommentSchema.model_validate(comment) for comment in comments])


@router.patch("/{comment_id}/", response_model=CommentSchema)
async def update_comment(
    comment_id: int,
    comment_data: CommentUpdateSchema,
    db: AsyncSession = Depends(get_db),
    current_user: CurrentUser = None,
):
    comment = await db.get(Comment, comment_id)
    if not comment:
        raise HTTPException(status_code=404, detail="Comment not found")

    if comment.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="You can only update your own comments")

    comment.content = comment_data.content
    await db.commit()
    await db.refresh(comment)

    return CommentSchema.model_validate(comment)


@router.delete("/{comment_id}/", status_code=204)
async def delete_comment(
    comment_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: CurrentUser = None,
):
    comment = await db.get(Comment, comment_id)
    if not comment:
        raise HTTPException(status_code=404, detail="Comment not found")

    if comment.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="You can only delete your own comments")

    await db.delete(comment)
    await db.commit()


@router.post("/{comment_id}/toggle-like/", status_code=200)
async def toggle_comment_like(
    comment_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: CurrentUser = None,
):
    comment = await db.get(Comment, comment_id)
    if not comment:
        raise HTTPException(status_code=404, detail="Comment not found")

    stmt = select(Like).where(
        Like.user_id == current_user.id,
        Like.likeable_id == comment_id,
        Like.likeable_type == "comment",
    )
    result = await db.execute(stmt)
    existing_like = result.scalars().first()

    if existing_like:
        await db.delete(existing_like)
        await db.commit()
        return {"detail": "Comment unliked successfully", "liked": False}
    else:
        like = Like(user_id=current_user.id, likeable_id=comment_id, likeable_type="comment")
        db.add(like)
        await db.commit()
        await db.refresh(like)
        return {"detail": "Comment liked successfully", "liked": True}
