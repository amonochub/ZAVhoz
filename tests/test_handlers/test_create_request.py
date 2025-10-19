"""Tests for create request handler."""

import pytest
from sqlalchemy import select

from models import User, Request, Priority, Status


class TestCreateRequestHandler:
    """Test request creation workflow."""

    async def _create_user(self, db_session: any, telegram_id: int = 100) -> User:
        """Helper to create test user."""
        user = User(telegram_id=telegram_id, username=f"user{telegram_id}")
        db_session.add(user)
        await db_session.commit()
        return user

    @pytest.mark.asyncio
    async def test_create_basic_request(self, db_session: any) -> None:
        """Test creating a basic request."""
        user = await self._create_user(db_session)

        request = Request(
            user_id=user.id,
            title="Test Request",
            description="This is a test request for creation",
            location="Test Room",
            priority=Priority.MEDIUM,
        )
        db_session.add(request)
        await db_session.commit()

        stmt = select(Request).where(Request.user_id == user.id)
        created = await db_session.scalar(stmt)

        assert created is not None
        assert created.title == "Test Request"

    @pytest.mark.asyncio
    async def test_request_with_high_priority(self, db_session: any) -> None:
        """Test creating request with high priority."""
        user = await self._create_user(db_session)

        request = Request(
            user_id=user.id,
            title="URGENT: Fire hazard",
            description="Emergency situation",
            location="Room 1",
            priority=Priority.HIGH,
        )
        db_session.add(request)
        await db_session.commit()

        stmt = select(Request).where(Request.priority == Priority.HIGH)
        urgent = await db_session.scalar(stmt)

        assert urgent is not None
        assert urgent.priority == Priority.HIGH

    @pytest.mark.asyncio
    async def test_user_can_create_multiple_requests(self, db_session: any) -> None:
        """Test that user can create multiple requests."""
        user = await self._create_user(db_session, telegram_id=200)

        for i in range(3):
            request = Request(
                user_id=user.id,
                title=f"Request {i+1}",
                description=f"Description for request {i+1}",
                location=f"Room {i+1}",
            )
            db_session.add(request)

        await db_session.commit()

        stmt = select(Request).where(Request.user_id == user.id)
        requests = (await db_session.execute(stmt)).scalars().all()

        assert len(requests) == 3

    @pytest.mark.asyncio
    async def test_request_starts_as_open(self, db_session: any) -> None:
        """Test that new request starts as OPEN."""
        user = await self._create_user(db_session)

        request = Request(
            user_id=user.id,
            title="New Request",
            description="Should be open initially",
            location="Room",
        )
        db_session.add(request)
        await db_session.commit()

        stmt = select(Request).where(Request.id == request.id)
        created = await db_session.scalar(stmt)

        assert created.status == Status.OPEN
