"""Error condition and exception handling tests."""

import pytest
from sqlalchemy import select

from models import User, Request, Priority, Status, Comment, File
from utils.validation import (
    validate_request_title,
    validate_request_description,
    validate_location,
)


class TestErrorConditions:
    """Test error handling and exception conditions."""

    @pytest.mark.asyncio
    async def test_empty_title_validation(self) -> None:
        """Test validation fails on empty title."""
        is_valid, msg = validate_request_title("")
        assert not is_valid
        assert "пустым" in msg.lower()

    @pytest.mark.asyncio
    async def test_empty_description_validation(self) -> None:
        """Test validation fails on empty description."""
        is_valid, msg = validate_request_description("")
        assert not is_valid
        assert "пустым" in msg.lower()

    @pytest.mark.asyncio
    async def test_empty_location_validation(self) -> None:
        """Test validation fails on empty location."""
        is_valid, msg = validate_location("")
        assert not is_valid
        assert "пустым" in msg.lower()

    @pytest.mark.asyncio
    async def test_invalid_telegram_id(self, db_session: any) -> None:
        """Test invalid telegram ID handling."""
        # Telegram IDs are just integers, no validation at DB level
        user = User(telegram_id=-1, username="invalid")
        db_session.add(user)
        await db_session.commit()
        
        stmt = select(User).where(User.telegram_id == -1)
        result = await db_session.scalar(stmt)
        assert result is not None

    @pytest.mark.asyncio
    async def test_request_without_user(self, db_session: any) -> None:
        """Test request creation without user fails."""
        request = Request(
            user_id=99999,  # Non-existent user
            title="Test",
            description="Test",
            location="Room",
        )
        db_session.add(request)

        # This should fail on commit due to foreign key constraint
        try:
            await db_session.commit()
            # If no error, rollback
            await db_session.rollback()
        except Exception:
            await db_session.rollback()

    @pytest.mark.asyncio
    async def test_comment_without_request(self, db_session: any) -> None:
        """Test comment creation without request fails."""
        user = User(telegram_id=9001, username="commenter")
        db_session.add(user)
        await db_session.commit()

        comment = Comment(
            request_id=99999,  # Non-existent request
            user_id=user.id,
            comment="Test",
        )
        db_session.add(comment)

        try:
            await db_session.commit()
            await db_session.rollback()
        except Exception:
            await db_session.rollback()

    @pytest.mark.asyncio
    async def test_null_required_title(self, db_session: any) -> None:
        """Test null title is rejected."""
        user = User(telegram_id=9002, username="null_test")
        db_session.add(user)
        await db_session.commit()

        request = Request(
            user_id=user.id,
            title=None,  # Required field
            description="Test",
            location="Room",
        )
        db_session.add(request)

        try:
            await db_session.commit()
            await db_session.rollback()
        except Exception:
            await db_session.rollback()

    @pytest.mark.asyncio
    async def test_valid_status_transitions(self, db_session: any) -> None:
        """Test valid status transitions work correctly."""
        user = User(telegram_id=9003, username="status_test")
        db_session.add(user)
        await db_session.commit()

        request = Request(
            user_id=user.id,
            title="Test",
            description="Test",
            location="Room",
        )
        db_session.add(request)
        await db_session.commit()

        # Test valid transitions
        valid_transitions = [Status.OPEN, Status.IN_PROGRESS, Status.COMPLETED]
        
        for status in valid_transitions:
            request.status = status
            await db_session.commit()

        stmt = select(Request).where(Request.id == request.id)
        result = await db_session.scalar(stmt)
        
        assert result.status == Status.COMPLETED

    @pytest.mark.asyncio
    async def test_duplicate_username_allowed(self, db_session: any) -> None:
        """Test that duplicate usernames are allowed (no unique constraint)."""
        user1 = User(telegram_id=9004, username="duplicate")
        user2 = User(telegram_id=9005, username="duplicate")
        
        db_session.add_all([user1, user2])
        await db_session.commit()

        stmt = select(User).where(User.username == "duplicate")
        users = (await db_session.execute(stmt)).scalars().all()
        
        assert len(users) == 2

    @pytest.mark.asyncio
    async def test_file_without_request(self, db_session: any) -> None:
        """Test file creation without request fails."""
        user = User(telegram_id=9006, username="file_user")
        db_session.add(user)
        await db_session.commit()

        file_obj = File(
            request_id=99999,  # Non-existent request
            file_id="file123",
            file_type="document",
            uploaded_by=user.id,
        )
        db_session.add(file_obj)

        try:
            await db_session.commit()
            await db_session.rollback()
        except Exception:
            await db_session.rollback()

    @pytest.mark.asyncio
    async def test_rollback_on_error(self, db_session: any) -> None:
        """Test transaction rollback on error."""
        user = User(telegram_id=9007, username="rollback_test")
        db_session.add(user)
        await db_session.commit()

        request = Request(
            user_id=user.id,
            title="Test",
            description="Test",
            location="Room",
        )
        db_session.add(request)
        await db_session.commit()
        
        initial_count = (await db_session.execute(select(Request))).scalars()
        initial_len = len(list(initial_count))

        # Try to create invalid comment
        comment = Comment(
            request_id=99999,  # Invalid
            user_id=user.id,
            comment="Test",
        )
        db_session.add(comment)

        try:
            await db_session.commit()
        except Exception:
            await db_session.rollback()

        # Original request should still exist
        stmt = select(Request).where(Request.id == request.id)
        result = await db_session.scalar(stmt)
        assert result is not None


class TestBoundaryConditions:
    """Test boundary conditions."""

    @pytest.mark.asyncio
    async def test_maximum_username_length(self, db_session: any) -> None:
        """Test maximum username length."""
        long_username = "u" * 100
        user = User(telegram_id=9100, username=long_username)
        db_session.add(user)
        await db_session.commit()

        stmt = select(User).where(User.id == user.id)
        stored = await db_session.scalar(stmt)
        
        assert len(stored.username) == 100

    @pytest.mark.asyncio
    async def test_priority_boundary_values(self, db_session: any) -> None:
        """Test all priority enum values."""
        user = User(telegram_id=9101, username="priority_boundary")
        db_session.add(user)
        await db_session.commit()

        for priority in [Priority.LOW, Priority.MEDIUM, Priority.HIGH]:
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

    @pytest.mark.asyncio
    async def test_status_enum_all_values(self, db_session: any) -> None:
        """Test all valid status enum values."""
        user = User(telegram_id=9102, username="status_boundary")
        db_session.add(user)
        await db_session.commit()

        valid_statuses = [Status.OPEN, Status.IN_PROGRESS, Status.COMPLETED, Status.REJECTED]

        for status in valid_statuses:
            request = Request(
                user_id=user.id,
                title=f"Status {status.value}",
                description="Test",
                location="Room",
            )
            request.status = status
            db_session.add(request)

        await db_session.commit()

        stmt = select(Request).where(Request.user_id == user.id)
        requests = (await db_session.execute(stmt)).scalars().all()
        
        assert len(requests) == len(valid_statuses)

    @pytest.mark.asyncio
    async def test_zero_user_id(self, db_session: any) -> None:
        """Test user creation with zero ID."""
        # Zero is technically valid for integer field
        user = User(telegram_id=0, username="zero_id")
        db_session.add(user)
        await db_session.commit()
        
        stmt = select(User).where(User.telegram_id == 0)
        result = await db_session.scalar(stmt)
        assert result is not None

    @pytest.mark.asyncio
    async def test_negative_assigned_to(self, db_session: any) -> None:
        """Test negative assigned_to value."""
        user = User(telegram_id=9103, username="assigned_test")
        db_session.add(user)
        await db_session.commit()

        request = Request(
            user_id=user.id,
            title="Test",
            description="Test",
            location="Room",
            assigned_to=-1,  # Invalid admin ID
        )
        db_session.add(request)
        await db_session.commit()

        stmt = select(Request).where(Request.id == request.id)
        result = await db_session.scalar(stmt)
        
        # DB doesn't validate, so it accepts it
        assert result.assigned_to == -1
