"""Edge case and stress tests."""

import pytest
from sqlalchemy import select

from models import User, Request, Priority, Status, Comment, File


class TestEdgeCases:
    """Test edge cases and boundary conditions."""

    @pytest.mark.asyncio
    async def test_very_long_request_title(self, db_session: any) -> None:
        """Test with maximum length title."""
        user = User(telegram_id=2000, username="edge_user")
        db_session.add(user)
        await db_session.commit()

        long_title = "A" * 100  # Max allowed
        request = Request(
            user_id=user.id,
            title=long_title,
            description="Test with long title",
            location="Room",
        )
        db_session.add(request)
        await db_session.commit()

        stmt = select(Request).where(Request.user_id == user.id)
        stored = await db_session.scalar(stmt)

        assert stored.title == long_title
        assert len(stored.title) == 100

    @pytest.mark.asyncio
    async def test_very_long_description(self, db_session: any) -> None:
        """Test with maximum length description."""
        user = User(telegram_id=2001, username="edge_user2")
        db_session.add(user)
        await db_session.commit()

        long_desc = "B" * 1000  # Max allowed
        request = Request(
            user_id=user.id,
            title="Title",
            description=long_desc,
            location="Room",
        )
        db_session.add(request)
        await db_session.commit()

        stmt = select(Request).where(Request.user_id == user.id)
        stored = await db_session.scalar(stmt)

        assert len(stored.description) == 1000

    @pytest.mark.asyncio
    async def test_stress_many_users(self, db_session: any) -> None:
        """Test creating many users."""
        users = [
            User(telegram_id=3000+i, username=f"stress_user_{i}")
            for i in range(50)
        ]
        db_session.add_all(users)
        await db_session.commit()

        stmt = select(User)
        all_users = (await db_session.execute(stmt)).scalars().all()

        assert len(all_users) >= 50

    @pytest.mark.asyncio
    async def test_stress_many_requests(self, db_session: any) -> None:
        """Test creating many requests."""
        user = User(telegram_id=4000, username="stress_requester")
        db_session.add(user)
        await db_session.commit()

        requests = [
            Request(
                user_id=user.id,
                title=f"Request {i}",
                description=f"Description {i}",
                location=f"Room {i}",
                priority=Priority.HIGH if i % 2 == 0 else Priority.LOW,
            )
            for i in range(100)
        ]
        db_session.add_all(requests)
        await db_session.commit()

        stmt = select(Request).where(Request.user_id == user.id)
        user_requests = (await db_session.execute(stmt)).scalars().all()

        assert len(user_requests) == 100

    @pytest.mark.asyncio
    async def test_null_optional_fields(self, db_session: any) -> None:
        """Test that optional fields can be null."""
        user = User(telegram_id=5000, username="optional_user")
        db_session.add(user)
        await db_session.commit()

        # Request with minimal data
        request = Request(
            user_id=user.id,
            title="Minimal",
            description="Minimal request",
            location="Room",
        )
        db_session.add(request)
        await db_session.commit()

        stmt = select(Request).where(Request.id == request.id)
        minimal = await db_session.scalar(stmt)

        assert minimal.assigned_to is None
        assert minimal.completed_at is None

    @pytest.mark.asyncio
    async def test_status_workflow_all_transitions(self, db_session: any) -> None:
        """Test all valid status transitions."""
        user = User(telegram_id=6000, username="workflow_user")
        db_session.add(user)
        await db_session.commit()

        request = Request(
            user_id=user.id,
            title="Workflow",
            description="Testing all statuses",
            location="Room",
        )
        db_session.add(request)
        await db_session.commit()

        # Test transitions
        transitions = [
            Status.OPEN,
            Status.IN_PROGRESS,
            Status.COMPLETED,
        ]

        for status in transitions:
            request.status = status
            await db_session.commit()

            stmt = select(Request).where(Request.id == request.id)
            current = await db_session.scalar(stmt)
            assert current.status == status

    @pytest.mark.asyncio
    async def test_comment_with_special_characters(self, db_session: any) -> None:
        """Test comment with special characters."""
        user = User(telegram_id=7000, username="special_user")
        db_session.add(user)
        await db_session.commit()

        request = Request(
            user_id=user.id,
            title="Special",
            description="Test",
            location="Room",
        )
        db_session.add(request)
        await db_session.commit()

        special_text = "Test with émojis 😀 and spëcial çhars! @#$%"
        comment = Comment(
            request_id=request.id,
            user_id=user.id,
            comment=special_text,
        )
        db_session.add(comment)
        await db_session.commit()

        stmt = select(Comment).where(Comment.id == comment.id)
        stored = await db_session.scalar(stmt)

        assert stored.comment == special_text

    @pytest.mark.asyncio
    async def test_priority_with_all_levels(self, db_session: any) -> None:
        """Test all priority levels."""
        user = User(telegram_id=8000, username="priority_user")
        db_session.add(user)
        await db_session.commit()

        priorities = [Priority.LOW, Priority.MEDIUM, Priority.HIGH]
        
        for priority in priorities:
            request = Request(
                user_id=user.id,
                title=f"Priority {priority.value}",
                description="Test",
                location="Room",
                priority=priority,
            )
            db_session.add(request)

        await db_session.commit()

        stmt = select(Request).where(Request.user_id == user.id)
        requests = (await db_session.execute(stmt)).scalars().all()

        assert len(requests) == 3
        priorities_found = [r.priority for r in requests]
        assert Priority.LOW in priorities_found
        assert Priority.MEDIUM in priorities_found
        assert Priority.HIGH in priorities_found
