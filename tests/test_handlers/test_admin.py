"""Tests for admin handler."""

import pytest
from sqlalchemy import select

from models import User, Request, Priority, Status


class TestAdminHandler:
    """Test admin functions."""

    async def _create_test_data(self, db_session: any) -> tuple:
        """Helper to create test users and requests."""
        # Create regular user
        user = User(telegram_id=500, username="regular_user", role="user")
        db_session.add(user)
        
        # Create admin
        admin = User(telegram_id=600, username="admin_user", role="admin")
        db_session.add(admin)
        
        await db_session.commit()

        # Create requests
        requests = []
        for i in range(3):
            req = Request(
                user_id=user.id,
                title=f"Request {i+1}",
                description=f"Description {i+1}",
                location=f"Room {i+1}",
                priority=Priority.HIGH if i == 0 else Priority.MEDIUM,
                status=Status.OPEN if i < 2 else Status.IN_PROGRESS,
            )
            db_session.add(req)
            requests.append(req)

        await db_session.commit()
        return user, admin, requests

    @pytest.mark.asyncio
    async def test_get_all_open_requests(self, db_session: any) -> None:
        """Test getting all open requests."""
        user, admin, requests = await self._create_test_data(db_session)

        stmt = select(Request).where(Request.status == Status.OPEN)
        open_requests = (await db_session.execute(stmt)).scalars().all()

        assert len(open_requests) == 2

    @pytest.mark.asyncio
    async def test_get_all_in_progress_requests(self, db_session: any) -> None:
        """Test getting in-progress requests."""
        user, admin, requests = await self._create_test_data(db_session)

        stmt = select(Request).where(Request.status == Status.IN_PROGRESS)
        progress = (await db_session.execute(stmt)).scalars().all()

        assert len(progress) == 1

    @pytest.mark.asyncio
    async def test_admin_can_assign_request(self, db_session: any) -> None:
        """Test admin assigning request to themselves."""
        user, admin, requests = await self._create_test_data(db_session)

        req = requests[0]
        req.assigned_to = admin.id
        await db_session.commit()

        stmt = select(Request).where(Request.id == req.id)
        assigned = await db_session.scalar(stmt)

        assert assigned.assigned_to == admin.id

    @pytest.mark.asyncio
    async def test_admin_can_update_status(self, db_session: any) -> None:
        """Test admin updating request status."""
        user, admin, requests = await self._create_test_data(db_session)

        req = requests[0]
        req.status = Status.COMPLETED
        await db_session.commit()

        stmt = select(Request).where(Request.id == req.id)
        updated = await db_session.scalar(stmt)

        assert updated.status == Status.COMPLETED

    @pytest.mark.asyncio
    async def test_get_high_priority_requests(self, db_session: any) -> None:
        """Test filtering high priority requests."""
        user, admin, requests = await self._create_test_data(db_session)

        stmt = select(Request).where(Request.priority == Priority.HIGH)
        urgent = (await db_session.execute(stmt)).scalars().all()

        assert len(urgent) == 1
        assert urgent[0].title == "Request 1"
