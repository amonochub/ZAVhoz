"""Tests for request actions handler."""

import pytest
from sqlalchemy import select

from models import User, Request, Status, Priority, Comment


class TestRequestActionsHandler:
    """Test request action workflows."""

    async def _create_test_data(self, db_session: any) -> tuple:
        """Helper to create test user and request."""
        user = User(telegram_id=1000, username="requester", role="user")
        admin = User(telegram_id=1001, username="admin", role="admin")
        db_session.add_all([user, admin])
        await db_session.commit()

        request = Request(
            user_id=user.id,
            title="Test Action Request",
            description="Testing request actions",
            location="Room 101",
            priority=Priority.HIGH,
        )
        db_session.add(request)
        await db_session.commit()

        return user, admin, request

    @pytest.mark.asyncio
    async def test_take_request_in_work(self, db_session: any) -> None:
        """Test admin taking request in work."""
        user, admin, request = await self._create_test_data(db_session)

        request.status = Status.IN_PROGRESS
        request.assigned_to = admin.id
        await db_session.commit()

        stmt = select(Request).where(Request.id == request.id)
        updated = await db_session.scalar(stmt)

        assert updated.status == Status.IN_PROGRESS
        assert updated.assigned_to == admin.id

    @pytest.mark.asyncio
    async def test_add_comment_to_request(self, db_session: any) -> None:
        """Test adding comment to request."""
        user, admin, request = await self._create_test_data(db_session)

        comment = Comment(
            request_id=request.id,
            user_id=admin.id,
            comment="Will start repair today",
        )
        db_session.add(comment)
        await db_session.commit()

        stmt = select(Comment).where(Comment.request_id == request.id)
        added = await db_session.scalar(stmt)

        assert added is not None
        assert added.comment == "Will start repair today"

    @pytest.mark.asyncio
    async def test_complete_request(self, db_session: any) -> None:
        """Test completing request."""
        user, admin, request = await self._create_test_data(db_session)

        request.status = Status.IN_PROGRESS
        request.assigned_to = admin.id
        await db_session.commit()

        request.status = Status.COMPLETED
        await db_session.commit()

        stmt = select(Request).where(Request.id == request.id)
        completed = await db_session.scalar(stmt)

        assert completed.status == Status.COMPLETED

    @pytest.mark.asyncio
    async def test_reject_request(self, db_session: any) -> None:
        """Test rejecting request."""
        user, admin, request = await self._create_test_data(db_session)

        request.status = Status.REJECTED
        request.assigned_to = admin.id
        await db_session.commit()

        # Add rejection reason comment
        comment = Comment(
            request_id=request.id,
            user_id=admin.id,
            comment="Not our responsibility",
        )
        db_session.add(comment)
        await db_session.commit()

        stmt = select(Request).where(Request.id == request.id)
        rejected = await db_session.scalar(stmt)

        assert rejected.status == Status.REJECTED

    @pytest.mark.asyncio
    async def test_reassign_request(self, db_session: any) -> None:
        """Test reassigning request to different admin."""
        user, admin, request = await self._create_test_data(db_session)

        other_admin = User(telegram_id=1002, username="other_admin", role="admin")
        db_session.add(other_admin)
        await db_session.commit()

        request.assigned_to = admin.id
        await db_session.commit()

        # Reassign
        request.assigned_to = other_admin.id
        await db_session.commit()

        stmt = select(Request).where(Request.id == request.id)
        reassigned = await db_session.scalar(stmt)

        assert reassigned.assigned_to == other_admin.id

    @pytest.mark.asyncio
    async def test_multiple_comments_on_request(self, db_session: any) -> None:
        """Test multiple comments being added to request."""
        user, admin, request = await self._create_test_data(db_session)

        comments_text = [
            "Taking this request",
            "Checking status",
            "Repair complete",
        ]

        for text in comments_text:
            comment = Comment(
                request_id=request.id,
                user_id=admin.id,
                comment=text,
            )
            db_session.add(comment)

        await db_session.commit()

        stmt = select(Comment).where(Comment.request_id == request.id)
        comments = (await db_session.execute(stmt)).scalars().all()

        assert len(comments) == 3
