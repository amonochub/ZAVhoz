"""Advanced scenario and complex workflow tests."""

import pytest
from sqlalchemy import select, and_

from models import User, Request, Status, Priority, Comment, File


class TestComplexWorkflows:
    """Test complex multi-step workflows."""

    @pytest.mark.asyncio
    async def test_full_request_lifecycle(self, db_session: any) -> None:
        """Test complete request from creation to completion."""
        # Create user and admin
        user = User(telegram_id=7000, username="lifecycle_user")
        admin = User(telegram_id=7001, username="lifecycle_admin", role="admin")
        db_session.add_all([user, admin])
        await db_session.commit()

        # Create request
        request = Request(
            user_id=user.id,
            title="Full Lifecycle",
            description="Complete workflow test",
            location="Room 101",
            priority=Priority.HIGH,
        )
        db_session.add(request)
        await db_session.commit()

        assert request.status == Status.OPEN

        # Admin takes it
        request.status = Status.IN_PROGRESS
        request.assigned_to = admin.id
        await db_session.commit()

        # Admin adds comments
        comments = [
            "Starting work",
            "Progress update",
            "Almost done",
        ]
        for comment_text in comments:
            comment = Comment(
                request_id=request.id,
                user_id=admin.id,
                comment=comment_text,
            )
            db_session.add(comment)

        await db_session.commit()

        # Complete request
        request.status = Status.COMPLETED
        await db_session.commit()

        # Verify final state
        stmt = select(Request).where(Request.id == request.id)
        final = await db_session.scalar(stmt)

        assert final.status == Status.COMPLETED
        assert final.assigned_to == admin.id
        assert final.priority == Priority.HIGH

        # Verify comments exist
        stmt = select(Comment).where(Comment.request_id == request.id)
        request_comments = (await db_session.execute(stmt)).scalars().all()
        assert len(request_comments) == 3

    @pytest.mark.asyncio
    async def test_multi_user_collaboration(self, db_session: any) -> None:
        """Test workflow with multiple users."""
        # Create multiple users
        requester = User(telegram_id=7100, username="requester")
        admin1 = User(telegram_id=7101, username="admin1", role="admin")
        admin2 = User(telegram_id=7102, username="admin2", role="admin")
        
        db_session.add_all([requester, admin1, admin2])
        await db_session.commit()

        # Create request
        request = Request(
            user_id=requester.id,
            title="Team Effort",
            description="Multiple admins working",
            location="Room",
        )
        db_session.add(request)
        await db_session.commit()

        # Admin 1 takes it
        request.assigned_to = admin1.id
        request.status = Status.IN_PROGRESS
        await db_session.commit()

        # Admin 1 adds comment
        comment1 = Comment(
            request_id=request.id,
            user_id=admin1.id,
            comment="Starting initial assessment",
        )
        db_session.add(comment1)
        await db_session.commit()

        # Reassign to Admin 2
        request.assigned_to = admin2.id
        comment2 = Comment(
            request_id=request.id,
            user_id=admin1.id,
            comment="Reassigning to admin2",
        )
        db_session.add(comment2)
        await db_session.commit()

        # Admin 2 completes it
        request.status = Status.COMPLETED
        comment3 = Comment(
            request_id=request.id,
            user_id=admin2.id,
            comment="Work completed successfully",
        )
        db_session.add(comment3)
        await db_session.commit()

        # Verify workflow
        stmt = select(Request).where(Request.id == request.id)
        final_request = await db_session.scalar(stmt)

        assert final_request.status == Status.COMPLETED
        assert final_request.assigned_to == admin2.id

        stmt = select(Comment).where(Comment.request_id == request.id)
        all_comments = (await db_session.execute(stmt)).scalars().all()
        assert len(all_comments) == 3

    @pytest.mark.asyncio
    async def test_request_rejection_workflow(self, db_session: any) -> None:
        """Test workflow where request is rejected."""
        user = User(telegram_id=7200, username="reject_user")
        admin = User(telegram_id=7201, username="reject_admin", role="admin")
        db_session.add_all([user, admin])
        await db_session.commit()

        request = Request(
            user_id=user.id,
            title="To Be Rejected",
            description="This will be rejected",
            location="Room",
        )
        db_session.add(request)
        await db_session.commit()

        # Admin reviews and rejects
        request.status = Status.IN_PROGRESS
        request.assigned_to = admin.id
        await db_session.commit()

        # Add rejection reason
        rejection_comment = Comment(
            request_id=request.id,
            user_id=admin.id,
            comment="Not our responsibility - facility issue",
        )
        db_session.add(rejection_comment)
        await db_session.commit()

        request.status = Status.REJECTED
        await db_session.commit()

        # Verify rejection
        stmt = select(Request).where(Request.id == request.id)
        rejected = await db_session.scalar(stmt)

        assert rejected.status == Status.REJECTED

        stmt = select(Comment).where(Comment.request_id == request.id)
        comments = (await db_session.execute(stmt)).scalars().all()
        assert len(comments) == 1
        assert "Not our responsibility" in comments[0].comment

    @pytest.mark.asyncio
    async def test_priority_escalation_workflow(self, db_session: any) -> None:
        """Test workflow where priority is escalated due to age."""
        user = User(telegram_id=7300, username="escalate_user")
        admin = User(telegram_id=7301, username="escalate_admin", role="admin")
        db_session.add_all([user, admin])
        await db_session.commit()

        # Create low priority request
        request = Request(
            user_id=user.id,
            title="Low Priority Task",
            description="Starts as low priority",
            location="Room",
            priority=Priority.LOW,
        )
        db_session.add(request)
        await db_session.commit()

        initial_priority = request.priority

        # After some time, escalate if unresolved
        request.priority = Priority.MEDIUM
        await db_session.commit()

        # Further escalate
        request.priority = Priority.HIGH
        await db_session.commit()

        # Verify escalation
        stmt = select(Request).where(Request.id == request.id)
        escalated = await db_session.scalar(stmt)

        assert initial_priority == Priority.LOW
        assert escalated.priority == Priority.HIGH

    @pytest.mark.asyncio
    async def test_request_with_files_and_comments(self, db_session: any) -> None:
        """Test request with both files and comments."""
        user = User(telegram_id=7400, username="file_comment_user")
        admin = User(telegram_id=7401, username="file_comment_admin", role="admin")
        db_session.add_all([user, admin])
        await db_session.commit()

        request = Request(
            user_id=user.id,
            title="Complex Request",
            description="With files and comments",
            location="Room",
        )
        db_session.add(request)
        await db_session.commit()

        # Add files
        for i in range(3):
            file_obj = File(
                request_id=request.id,
                file_id=f"file_{i}",
                file_type="document",
                uploaded_by=user.id,
            )
            db_session.add(file_obj)

        await db_session.commit()

        # Add comments
        for i in range(2):
            comment = Comment(
                request_id=request.id,
                user_id=admin.id,
                comment=f"Comment {i}: Analysis update",
            )
            db_session.add(comment)

        await db_session.commit()

        # Verify relationships
        stmt = select(File).where(File.request_id == request.id)
        files = (await db_session.execute(stmt)).scalars().all()
        assert len(files) == 3

        stmt = select(Comment).where(Comment.request_id == request.id)
        comments = (await db_session.execute(stmt)).scalars().all()
        assert len(comments) == 2


class TestConcurrentScenarios:
    """Test concurrent and parallel scenarios."""

    @pytest.mark.asyncio
    async def test_multiple_open_requests(self, db_session: any) -> None:
        """Test multiple open requests from same user."""
        user = User(telegram_id=7500, username="multi_request_user")
        db_session.add(user)
        await db_session.commit()

        # Create multiple requests
        for i in range(5):
            request = Request(
                user_id=user.id,
                title=f"Request {i}",
                description=f"Request number {i}",
                location=f"Room {i}",
                priority=Priority.LOW if i % 2 == 0 else Priority.HIGH,
            )
            db_session.add(request)

        await db_session.commit()

        # Verify all created
        stmt = select(Request).where(Request.user_id == user.id)
        requests = (await db_session.execute(stmt)).scalars().all()
        assert len(requests) == 5

        # Count by priority
        high_priority = [r for r in requests if r.priority == Priority.HIGH]
        low_priority = [r for r in requests if r.priority == Priority.LOW]

        assert len(high_priority) == 2
        assert len(low_priority) == 3

    @pytest.mark.asyncio
    async def test_multiple_admins_on_different_requests(self, db_session: any) -> None:
        """Test multiple admins working on different requests."""
        user = User(telegram_id=7600, username="multi_admin_user")
        admin1 = User(telegram_id=7601, username="admin1", role="admin")
        admin2 = User(telegram_id=7602, username="admin2", role="admin")
        admin3 = User(telegram_id=7603, username="admin3", role="admin")

        db_session.add_all([user, admin1, admin2, admin3])
        await db_session.commit()

        # Create 3 requests
        admins = [admin1, admin2, admin3]
        for i, admin in enumerate(admins):
            request = Request(
                user_id=user.id,
                title=f"Admin {admin.id} Request",
                description="Assigned to specific admin",
                location=f"Zone {i}",
                status=Status.IN_PROGRESS,
                assigned_to=admin.id,
            )
            db_session.add(request)

        await db_session.commit()

        # Verify each admin has one
        for admin in admins:
            stmt = select(Request).where(Request.assigned_to == admin.id)
            admin_requests = (await db_session.execute(stmt)).scalars().all()
            assert len(admin_requests) == 1

    @pytest.mark.asyncio
    async def test_bulk_status_updates(self, db_session: any) -> None:
        """Test updating multiple requests' status."""
        user = User(telegram_id=7700, username="bulk_user")
        admin = User(telegram_id=7701, username="bulk_admin", role="admin")
        db_session.add_all([user, admin])
        await db_session.commit()

        # Create multiple requests
        for i in range(5):
            request = Request(
                user_id=user.id,
                title=f"Bulk {i}",
                description="Bulk update test",
                location="Room",
                status=Status.OPEN,
            )
            db_session.add(request)

        await db_session.commit()

        # Get all requests and update them
        stmt = select(Request).where(Request.user_id == user.id)
        requests = (await db_session.execute(stmt)).scalars().all()

        for req in requests:
            req.status = Status.IN_PROGRESS
            req.assigned_to = admin.id

        await db_session.commit()

        # Verify all updated
        stmt = select(Request).where(
            and_(
                Request.status == Status.IN_PROGRESS,
                Request.user_id == user.id
            )
        )
        updated = (await db_session.execute(stmt)).scalars().all()
        assert len(updated) == 5
