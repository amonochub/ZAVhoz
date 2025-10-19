"""Tests for Request model."""

import pytest
from sqlalchemy import select

from models import User, Request, Priority, Status


class TestRequestModel:
    """Test Request model creation and properties."""

    async def _create_user(self, db_session: any, telegram_id: int = 123) -> User:
        """Helper to create test user."""
        user = User(telegram_id=telegram_id, username=f"user{telegram_id}")
        db_session.add(user)
        await db_session.commit()
        return user

    @pytest.mark.asyncio
    async def test_create_request(self, db_session: any) -> None:
        """Test creating a request."""
        user = await self._create_user(db_session)

        request = Request(
            user_id=user.id,
            title="Fix computer",
            description="Computer is not starting",
            location="Room 101",
            priority=Priority.HIGH,
            status=Status.OPEN,
        )
        db_session.add(request)
        await db_session.commit()

        # Retrieve and verify
        stmt = select(Request).where(Request.id == request.id)
        retrieved = await db_session.scalar(stmt)

        assert retrieved is not None
        assert retrieved.title == "Fix computer"
        assert retrieved.priority == Priority.HIGH
        assert retrieved.status == Status.OPEN
        assert retrieved.user_id == user.id

    @pytest.mark.asyncio
    async def test_request_default_status(self, db_session: any) -> None:
        """Test request default status is OPEN."""
        user = await self._create_user(db_session)

        request = Request(
            user_id=user.id,
            title="Default status",
            description="Testing default status",
            location="Room 202",
        )
        db_session.add(request)
        await db_session.commit()

        stmt = select(Request).where(Request.id == request.id)
        retrieved = await db_session.scalar(stmt)

        assert retrieved.status == Status.OPEN
        assert retrieved.priority == Priority.MEDIUM

    @pytest.mark.asyncio
    async def test_request_priority_levels(self, db_session: any) -> None:
        """Test all priority levels."""
        user = await self._create_user(db_session)

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

        # Verify all priorities
        stmt = select(Request).where(Request.user_id == user.id)
        requests = (await db_session.execute(stmt)).scalars().all()
        assert len(requests) == 3

    @pytest.mark.asyncio
    async def test_request_status_transitions(self, db_session: any) -> None:
        """Test request status transitions."""
        user = await self._create_user(db_session)

        request = Request(
            user_id=user.id,
            title="Status transition",
            description="Test",
            location="Room",
        )
        db_session.add(request)
        await db_session.commit()

        # Transition: OPEN -> IN_PROGRESS
        request.status = Status.IN_PROGRESS
        await db_session.commit()

        stmt = select(Request).where(Request.id == request.id)
        retrieved = await db_session.scalar(stmt)
        assert retrieved.status == Status.IN_PROGRESS

        # Transition: IN_PROGRESS -> COMPLETED
        retrieved.status = Status.COMPLETED
        await db_session.commit()

        stmt = select(Request).where(Request.id == request.id)
        retrieved = await db_session.scalar(stmt)
        assert retrieved.status == Status.COMPLETED

    @pytest.mark.asyncio
    async def test_request_assignment(self, db_session: any) -> None:
        """Test assigning request to admin."""
        user = await self._create_user(db_session, telegram_id=111)
        admin = await self._create_user(db_session, telegram_id=222)

        request = Request(
            user_id=user.id,
            title="Assigned request",
            description="Test",
            location="Room",
        )
        db_session.add(request)
        await db_session.commit()

        # Assign to admin
        request.assigned_to = admin.id
        await db_session.commit()

        stmt = select(Request).where(Request.id == request.id)
        retrieved = await db_session.scalar(stmt)
        assert retrieved.assigned_to == admin.id
