"""File upload and workflow tests."""

import pytest
from sqlalchemy import select

from models import User, Request, File, Priority


class TestFileWorkflows:
    """Test file attachment and workflow scenarios."""

    async def _create_test_data(self, db_session: any) -> tuple:
        """Helper to create test user and request."""
        user = User(telegram_id=5000, username="file_user")
        db_session.add(user)
        await db_session.commit()

        request = Request(
            user_id=user.id,
            title="Request with Files",
            description="Testing file workflows",
            location="Room 101",
        )
        db_session.add(request)
        await db_session.commit()

        return user, request

    @pytest.mark.asyncio
    async def test_single_file_upload(self, db_session: any) -> None:
        """Test uploading single file."""
        user, request = await self._create_test_data(db_session)

        file_obj = File(
            request_id=request.id,
            file_id="file_123",
            file_type="document",
            uploaded_by=user.id,
        )
        db_session.add(file_obj)
        await db_session.commit()

        stmt = select(File).where(File.request_id == request.id)
        files = (await db_session.execute(stmt)).scalars().all()

        assert len(files) == 1
        assert files[0].file_id == "file_123"

    @pytest.mark.asyncio
    async def test_multiple_files_same_request(self, db_session: any) -> None:
        """Test uploading multiple files to same request."""
        user, request = await self._create_test_data(db_session)

        file_ids = ["file_001", "file_002", "file_003", "file_004"]
        
        for file_id in file_ids:
            file_obj = File(
                request_id=request.id,
                file_id=file_id,
                file_type="document",
                uploaded_by=user.id,
            )
            db_session.add(file_obj)

        await db_session.commit()

        stmt = select(File).where(File.request_id == request.id)
        files = (await db_session.execute(stmt)).scalars().all()

        assert len(files) == 4
        found_ids = [f.file_id for f in files]
        assert all(file_id in found_ids for file_id in file_ids)

    @pytest.mark.asyncio
    async def test_different_file_types(self, db_session: any) -> None:
        """Test uploading different file types."""
        user, request = await self._create_test_data(db_session)

        file_types = ["document", "image", "video", "audio", "application"]
        
        for i, file_type in enumerate(file_types):
            file_obj = File(
                request_id=request.id,
                file_id=f"file_{i}",
                file_type=file_type,
                uploaded_by=user.id,
            )
            db_session.add(file_obj)

        await db_session.commit()

        stmt = select(File).where(File.request_id == request.id)
        files = (await db_session.execute(stmt)).scalars().all()

        assert len(files) == 5
        types_found = [f.file_type for f in files]
        assert all(ft in types_found for ft in file_types)

    @pytest.mark.asyncio
    async def test_file_with_different_uploaders(self, db_session: any) -> None:
        """Test files uploaded by different users."""
        user1 = User(telegram_id=5001, username="uploader_1")
        user2 = User(telegram_id=5002, username="uploader_2")
        db_session.add_all([user1, user2])
        await db_session.commit()

        request = Request(
            user_id=user1.id,
            title="Multi-uploader files",
            description="Test",
            location="Room",
        )
        db_session.add(request)
        await db_session.commit()

        # User1 uploads file
        file1 = File(
            request_id=request.id,
            file_id="file_u1",
            file_type="document",
            uploaded_by=user1.id,
        )
        
        # User2 uploads file to same request
        file2 = File(
            request_id=request.id,
            file_id="file_u2",
            file_type="image",
            uploaded_by=user2.id,
        )
        
        db_session.add_all([file1, file2])
        await db_session.commit()

        stmt = select(File).where(File.request_id == request.id)
        files = (await db_session.execute(stmt)).scalars().all()

        assert len(files) == 2
        uploaders = [f.uploaded_by for f in files]
        assert user1.id in uploaders
        assert user2.id in uploaders

    @pytest.mark.asyncio
    async def test_multiple_requests_same_user_with_files(self, db_session: any) -> None:
        """Test multiple requests from same user with files."""
        user = User(telegram_id=5003, username="multi_request_user")
        db_session.add(user)
        await db_session.commit()

        # Create 3 requests
        requests = []
        for i in range(3):
            req = Request(
                user_id=user.id,
                title=f"Request {i}",
                description=f"Desc {i}",
                location=f"Room {i}",
            )
            db_session.add(req)
            requests.append(req)

        await db_session.commit()

        # Upload files to each request
        for i, req in enumerate(requests):
            for j in range(2):
                file_obj = File(
                    request_id=req.id,
                    file_id=f"file_{i}_{j}",
                    file_type="document",
                    uploaded_by=user.id,
                )
                db_session.add(file_obj)

        await db_session.commit()

        # Verify files
        stmt = select(File).where(File.uploaded_by == user.id)
        all_files = (await db_session.execute(stmt)).scalars().all()

        assert len(all_files) == 6  # 3 requests × 2 files each

    @pytest.mark.asyncio
    async def test_file_id_format_variations(self, db_session: any) -> None:
        """Test various file ID formats."""
        user, request = await self._create_test_data(db_session)

        file_ids = [
            "123456789",  # Numeric
            "file_123_abc",  # Alphanumeric
            "FILE_UPPERCASE",  # Uppercase
            "file-with-dash",  # With dash
            "file.with.dots",  # With dots
        ]

        for file_id in file_ids:
            file_obj = File(
                request_id=request.id,
                file_id=file_id,
                file_type="document",
                uploaded_by=user.id,
            )
            db_session.add(file_obj)

        await db_session.commit()

        stmt = select(File).where(File.request_id == request.id)
        files = (await db_session.execute(stmt)).scalars().all()

        assert len(files) == 5
        stored_ids = [f.file_id for f in files]
        assert all(fid in stored_ids for fid in file_ids)

    @pytest.mark.asyncio
    async def test_file_attachment_with_priority_request(self, db_session: any) -> None:
        """Test file attachment to high-priority request."""
        user = User(telegram_id=5004, username="priority_file_user")
        db_session.add(user)
        await db_session.commit()

        request = Request(
            user_id=user.id,
            title="High Priority Request",
            description="Urgent",
            location="Room",
            priority=Priority.HIGH,
        )
        db_session.add(request)
        await db_session.commit()

        # Add multiple files
        for i in range(3):
            file_obj = File(
                request_id=request.id,
                file_id=f"urgent_file_{i}",
                file_type="document",
                uploaded_by=user.id,
            )
            db_session.add(file_obj)

        await db_session.commit()

        stmt = select(Request).where(Request.id == request.id)
        req = await db_session.scalar(stmt)

        assert req.priority == Priority.HIGH

        stmt = select(File).where(File.request_id == request.id)
        files = (await db_session.execute(stmt)).scalars().all()

        assert len(files) == 3

    @pytest.mark.asyncio
    async def test_stress_many_files(self, db_session: any) -> None:
        """Test uploading many files to single request."""
        user, request = await self._create_test_data(db_session)

        # Upload 50 files
        for i in range(50):
            file_obj = File(
                request_id=request.id,
                file_id=f"file_{i:03d}",
                file_type="document",
                uploaded_by=user.id,
            )
            db_session.add(file_obj)

        await db_session.commit()

        stmt = select(File).where(File.request_id == request.id)
        files = (await db_session.execute(stmt)).scalars().all()

        assert len(files) == 50
