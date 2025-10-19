"""Integration tests for complete request workflow."""

import pytest
from sqlalchemy import select

from models import User, Request, Priority, Status


class TestRequestWorkflow:
    """Test complete request lifecycle."""

    @pytest.mark.asyncio
    async def test_user_creates_request_workflow(self, db_session: any) -> None:
        """Test complete workflow: user creates request."""
        # Step 1: Create user
        user = User(
            telegram_id=111111,
            username="requester",
            first_name="John",
            role="user",
        )
        db_session.add(user)
        await db_session.commit()

        # Step 2: Create request
        request = Request(
            user_id=user.id,
            title="Broken printer",
            description="Printer in room 205 is not working",
            location="Room 205",
            priority=Priority.MEDIUM,
        )
        db_session.add(request)
        await db_session.commit()

        # Step 3: Verify request exists
        stmt = select(Request).where(Request.user_id == user.id)
        user_requests = (await db_session.execute(stmt)).scalars().all()
        assert len(user_requests) == 1
        assert user_requests[0].status == Status.OPEN

    @pytest.mark.asyncio
    async def test_admin_accepts_and_completes_request(self, db_session: any) -> None:
        """Test admin workflow: accept and complete request."""
        # Setup: Create user and admin
        user = User(telegram_id=222222, username="user", role="user")
        admin = User(telegram_id=333333, username="admin", role="admin")
        db_session.add_all([user, admin])
        await db_session.commit()

        # Create request
        request = Request(
            user_id=user.id,
            title="Broken chair",
            description="Office chair is broken",
            location="Room 101",
            priority=Priority.HIGH,
        )
        db_session.add(request)
        await db_session.commit()

        # Admin accepts: assigns to themselves
        request.assigned_to = admin.id
        request.status = Status.IN_PROGRESS
        await db_session.commit()

        # Verify assignment
        stmt = select(Request).where(Request.id == request.id)
        retrieved = await db_session.scalar(stmt)
        assert retrieved.assigned_to == admin.id
        assert retrieved.status == Status.IN_PROGRESS

        # Admin completes: marks as done
        retrieved.status = Status.COMPLETED
        await db_session.commit()

        # Verify completion
        stmt = select(Request).where(Request.id == request.id)
        completed = await db_session.scalar(stmt)
        assert completed.status == Status.COMPLETED

    @pytest.mark.asyncio
    async def test_multiple_users_multiple_requests(self, db_session: any) -> None:
        """Test multiple users creating multiple requests."""
        # Create 3 users
        users = []
        for i in range(1, 4):
            user = User(
                telegram_id=444444 + i,
                username=f"user{i}",
                first_name=f"User {i}",
            )
            db_session.add(user)
            users.append(user)

        await db_session.commit()

        # Each user creates 2 requests
        for user in users:
            for j in range(2):
                request = Request(
                    user_id=user.id,
                    title=f"Request {j+1} from {user.username}",
                    description="Test request",
                    location=f"Room {j+1}00",
                    priority=Priority.MEDIUM if j == 0 else Priority.LOW,
                )
                db_session.add(request)

        await db_session.commit()

        # Verify totals
        stmt = select(Request)
        all_requests = (await db_session.execute(stmt)).scalars().all()
        assert len(all_requests) == 6

        # Verify user's requests
        for user in users:
            stmt = select(Request).where(Request.user_id == user.id)
            user_requests = (await db_session.execute(stmt)).scalars().all()
            assert len(user_requests) == 2

    @pytest.mark.asyncio
    async def test_request_rejection_workflow(self, db_session: any) -> None:
        """Test admin rejecting a request."""
        user = User(telegram_id=555555, username="user")
        admin = User(telegram_id=666666, username="admin", role="admin")
        db_session.add_all([user, admin])
        await db_session.commit()

        request = Request(
            user_id=user.id,
            title="Invalid request",
            description="Test",
            location="Room",
            priority=Priority.LOW,
        )
        db_session.add(request)
        await db_session.commit()

        # Admin rejects
        request.status = Status.REJECTED
        request.assigned_to = admin.id
        await db_session.commit()

        stmt = select(Request).where(Request.id == request.id)
        retrieved = await db_session.scalar(stmt)
        assert retrieved.status == Status.REJECTED

    @pytest.mark.asyncio
    async def test_high_priority_request_handling(self, db_session: any) -> None:
        """Test handling of high priority requests."""
        user = User(telegram_id=777777, username="user")
        admin = User(telegram_id=888888, username="admin", role="admin")
        db_session.add_all([user, admin])
        await db_session.commit()

        # Create high priority request
        urgent_request = Request(
            user_id=user.id,
            title="CRITICAL: No power",
            description="Building lost power",
            location="Main Hall",
            priority=Priority.HIGH,
        )
        db_session.add(urgent_request)
        await db_session.commit()

        # Verify it's marked as high priority
        stmt = select(Request).where(Request.priority == Priority.HIGH)
        high_priority = (await db_session.execute(stmt)).scalars().all()
        assert len(high_priority) > 0
        assert high_priority[0].title == "CRITICAL: No power"
