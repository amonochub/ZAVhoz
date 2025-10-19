"""Tests for Comment model."""

import pytest
from sqlalchemy import select

from models import User, Request, Comment


class TestCommentModel:
    """Test Comment model creation and properties."""

    async def _create_request(self, db_session: any) -> Request:
        """Helper to create test request."""
        user = User(telegram_id=800, username="commenter")
        db_session.add(user)
        await db_session.commit()

        request = Request(
            user_id=user.id,
            title="Request for comments",
            description="Test",
            location="Room",
        )
        db_session.add(request)
        await db_session.commit()

        return request

    @pytest.mark.asyncio
    async def test_create_comment(self, db_session: any) -> None:
        """Test creating a comment."""
        request = await self._create_request(db_session)

        comment = Comment(
            request_id=request.id,
            user_id=request.user_id,
            comment="This is a test comment",
        )
        db_session.add(comment)
        await db_session.commit()

        stmt = select(Comment).where(Comment.request_id == request.id)
        created = await db_session.scalar(stmt)

        assert created is not None
        assert created.comment == "This is a test comment"

    @pytest.mark.asyncio
    async def test_multiple_comments_per_request(self, db_session: any) -> None:
        """Test multiple comments on request."""
        request = await self._create_request(db_session)

        for i in range(3):
            comment = Comment(
                request_id=request.id,
                user_id=request.user_id,
                comment=f"Comment {i+1}",
            )
            db_session.add(comment)

        await db_session.commit()

        stmt = select(Comment).where(Comment.request_id == request.id)
        comments = (await db_session.execute(stmt)).scalars().all()

        assert len(comments) == 3

    @pytest.mark.asyncio
    async def test_comment_timestamps(self, db_session: any) -> None:
        """Test comment creation timestamp."""
        request = await self._create_request(db_session)

        comment = Comment(
            request_id=request.id,
            user_id=request.user_id,
            comment="Timestamped comment",
        )
        db_session.add(comment)
        await db_session.commit()

        stmt = select(Comment).where(Comment.id == comment.id)
        created = await db_session.scalar(stmt)

        assert created.created_at is not None
