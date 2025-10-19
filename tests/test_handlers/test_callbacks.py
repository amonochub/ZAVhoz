"""Tests for callback query handlers."""

import pytest
from sqlalchemy import select

from models import User, Request, Status, Priority


class TestCallbackHandlers:
    """Test callback query and state machine handlers."""

    async def _create_test_data(self, db_session: any) -> tuple:
        """Helper to create test user and request."""
        user = User(telegram_id=6000, username="callback_user")
        admin = User(telegram_id=6001, username="callback_admin", role="admin")
        db_session.add_all([user, admin])
        await db_session.commit()

        request = Request(
            user_id=user.id,
            title="Test Callback Request",
            description="Testing callback workflows",
            location="Room 101",
            priority=Priority.MEDIUM,
        )
        db_session.add(request)
        await db_session.commit()

        return user, admin, request

    @pytest.mark.asyncio
    async def test_request_status_callback(self, db_session: any) -> None:
        """Test callback for status change."""
        user, admin, request = await self._create_test_data(db_session)

        # Simulate callback for status change
        request.status = Status.IN_PROGRESS
        request.assigned_to = admin.id
        await db_session.commit()

        stmt = select(Request).where(Request.id == request.id)
        updated = await db_session.scalar(stmt)

        assert updated.status == Status.IN_PROGRESS
        assert updated.assigned_to == admin.id

    @pytest.mark.asyncio
    async def test_priority_change_callback(self, db_session: any) -> None:
        """Test callback for priority change."""
        user, admin, request = await self._create_test_data(db_session)

        original_priority = request.priority
        request.priority = Priority.HIGH
        await db_session.commit()

        stmt = select(Request).where(Request.id == request.id)
        updated = await db_session.scalar(stmt)

        assert original_priority != Priority.HIGH
        assert updated.priority == Priority.HIGH

    @pytest.mark.asyncio
    async def test_request_completion_callback(self, db_session: any) -> None:
        """Test callback for request completion."""
        user, admin, request = await self._create_test_data(db_session)

        # Move through states: OPEN -> IN_PROGRESS -> COMPLETED
        request.status = Status.IN_PROGRESS
        request.assigned_to = admin.id
        await db_session.commit()

        request.status = Status.COMPLETED
        await db_session.commit()

        stmt = select(Request).where(Request.id == request.id)
        completed = await db_session.scalar(stmt)

        assert completed.status == Status.COMPLETED
        assert completed.assigned_to == admin.id

    @pytest.mark.asyncio
    async def test_cancel_in_progress_request(self, db_session: any) -> None:
        """Test canceling (rejecting) an in-progress request."""
        user, admin, request = await self._create_test_data(db_session)

        request.status = Status.IN_PROGRESS
        await db_session.commit()

        # Admin cancels the request
        request.status = Status.REJECTED
        await db_session.commit()

        stmt = select(Request).where(Request.id == request.id)
        cancelled = await db_session.scalar(stmt)

        assert cancelled.status == Status.REJECTED

    @pytest.mark.asyncio
    async def test_reassign_callback(self, db_session: any) -> None:
        """Test callback for request reassignment."""
        user, admin, request = await self._create_test_data(db_session)

        admin2 = User(telegram_id=6002, username="callback_admin2", role="admin")
        db_session.add(admin2)
        await db_session.commit()

        # Initial assignment
        request.assigned_to = admin.id
        await db_session.commit()

        # Reassign
        request.assigned_to = admin2.id
        await db_session.commit()

        stmt = select(Request).where(Request.id == request.id)
        reassigned = await db_session.scalar(stmt)

        assert reassigned.assigned_to == admin2.id

    @pytest.mark.asyncio
    async def test_multiple_status_transitions(self, db_session: any) -> None:
        """Test multiple status transitions via callbacks."""
        user, admin, request = await self._create_test_data(db_session)

        transitions = [
            Status.OPEN,
            Status.IN_PROGRESS,
            Status.COMPLETED,
        ]

        for status in transitions:
            request.status = status
            await db_session.commit()

        stmt = select(Request).where(Request.id == request.id)
        final = await db_session.scalar(stmt)

        assert final.status == Status.COMPLETED


class TestStateManagement:
    """Test state machine workflows."""

    @pytest.mark.asyncio
    async def test_new_request_state(self, db_session: any) -> None:
        """Test initial state of new request."""
        user = User(telegram_id=6100, username="state_user")
        db_session.add(user)
        await db_session.commit()

        request = Request(
            user_id=user.id,
            title="New Request",
            description="Testing initial state",
            location="Room",
        )
        db_session.add(request)
        await db_session.commit()

        stmt = select(Request).where(Request.id == request.id)
        stored = await db_session.scalar(stmt)

        assert stored.status == Status.OPEN
        assert stored.assigned_to is None

    @pytest.mark.asyncio
    async def test_assignment_state_transition(self, db_session: any) -> None:
        """Test request state when assigned."""
        user = User(telegram_id=6101, username="state_user2")
        admin = User(telegram_id=6102, username="state_admin", role="admin")
        db_session.add_all([user, admin])
        await db_session.commit()

        request = Request(
            user_id=user.id,
            title="Request",
            description="Test",
            location="Room",
        )
        db_session.add(request)
        await db_session.commit()

        # Assign to admin
        request.assigned_to = admin.id
        request.status = Status.IN_PROGRESS
        await db_session.commit()

        stmt = select(Request).where(Request.id == request.id)
        result = await db_session.scalar(stmt)

        assert result.status == Status.IN_PROGRESS
        assert result.assigned_to == admin.id

    @pytest.mark.asyncio
    async def test_completion_state_transition(self, db_session: any) -> None:
        """Test transition to completed state."""
        user = User(telegram_id=6103, username="complete_user")
        admin = User(telegram_id=6104, username="complete_admin", role="admin")
        db_session.add_all([user, admin])
        await db_session.commit()

        request = Request(
            user_id=user.id,
            title="Complete Request",
            description="Test",
            location="Room",
        )
        db_session.add(request)
        await db_session.commit()

        # Workflow: OPEN -> IN_PROGRESS -> COMPLETED
        request.assigned_to = admin.id
        request.status = Status.IN_PROGRESS
        await db_session.commit()

        request.status = Status.COMPLETED
        await db_session.commit()

        stmt = select(Request).where(Request.id == request.id)
        completed = await db_session.scalar(stmt)

        assert completed.status == Status.COMPLETED
        assert completed.assigned_to == admin.id


class TestPriorityHandling:
    """Test priority-based logic and callbacks."""

    @pytest.mark.asyncio
    async def test_high_priority_filtering(self, db_session: any) -> None:
        """Test filtering high priority requests."""
        user = User(telegram_id=6200, username="priority_user")
        db_session.add(user)
        await db_session.commit()

        # Create requests with different priorities
        for i, priority in enumerate([Priority.LOW, Priority.MEDIUM, Priority.HIGH]):
            request = Request(
                user_id=user.id,
                title=f"Request {i}",
                description=f"Priority: {priority.value}",
                location="Room",
                priority=priority,
            )
            db_session.add(request)

        await db_session.commit()

        stmt = select(Request).where(Request.priority == Priority.HIGH)
        high_priority = (await db_session.execute(stmt)).scalars().all()

        assert len(high_priority) == 1
        assert high_priority[0].priority == Priority.HIGH

    @pytest.mark.asyncio
    async def test_priority_escalation(self, db_session: any) -> None:
        """Test escalating request priority."""
        user = User(telegram_id=6201, username="escalate_user")
        db_session.add(user)
        await db_session.commit()

        request = Request(
            user_id=user.id,
            title="Escalating Request",
            description="Start low, go high",
            location="Room",
            priority=Priority.LOW,
        )
        db_session.add(request)
        await db_session.commit()

        # Escalate priority
        request.priority = Priority.MEDIUM
        await db_session.commit()

        request.priority = Priority.HIGH
        await db_session.commit()

        stmt = select(Request).where(Request.id == request.id)
        final = await db_session.scalar(stmt)

        assert final.priority == Priority.HIGH

    @pytest.mark.asyncio
    async def test_priority_with_status(self, db_session: any) -> None:
        """Test priority combined with status."""
        user = User(telegram_id=6202, username="priority_status_user")
        admin = User(telegram_id=6203, username="priority_status_admin", role="admin")
        db_session.add_all([user, admin])
        await db_session.commit()

        request = Request(
            user_id=user.id,
            title="Priority Status",
            description="Test",
            location="Room",
            priority=Priority.HIGH,
            status=Status.OPEN,
        )
        db_session.add(request)
        await db_session.commit()

        # Assign and check both priority and status
        request.status = Status.IN_PROGRESS
        request.assigned_to = admin.id
        await db_session.commit()

        stmt = select(Request).where(Request.id == request.id)
        result = await db_session.scalar(stmt)

        assert result.priority == Priority.HIGH
        assert result.status == Status.IN_PROGRESS
        assert result.assigned_to == admin.id
