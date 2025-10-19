"""Tests for validation utilities."""

import pytest

from utils.validation import (
    validate_request_title,
    validate_request_description,
    validate_location,
    validate_comment,
    sanitize_text,
    RateLimiter,
)


class TestValidateRequestTitle:
    """Test request title validation."""

    def test_valid_title(self) -> None:
        """Test valid title."""
        is_valid, msg = validate_request_title("Repair computer")
        assert is_valid is True
        assert msg == ""

    def test_empty_title(self) -> None:
        """Test empty title."""
        is_valid, msg = validate_request_title("")
        assert is_valid is False
        assert "empty" in msg.lower()

    def test_whitespace_only_title(self) -> None:
        """Test whitespace-only title."""
        is_valid, msg = validate_request_title("   ")
        assert is_valid is False

    def test_too_short_title(self) -> None:
        """Test too short title."""
        is_valid, msg = validate_request_title("ab")
        assert is_valid is False
        assert "3 characters" in msg

    def test_too_long_title(self) -> None:
        """Test too long title."""
        long_title = "A" * 101
        is_valid, msg = validate_request_title(long_title)
        assert is_valid is False
        assert "100" in msg

    def test_boundary_title_min(self) -> None:
        """Test minimum valid title."""
        is_valid, msg = validate_request_title("abc")
        assert is_valid is True

    def test_boundary_title_max(self) -> None:
        """Test maximum valid title."""
        is_valid, msg = validate_request_title("A" * 100)
        assert is_valid is True


class TestValidateRequestDescription:
    """Test request description validation."""

    def test_valid_description(self) -> None:
        """Test valid description."""
        is_valid, msg = validate_request_description("Computer is not turning on, showing error")
        assert is_valid is True
        assert msg == ""

    def test_empty_description(self) -> None:
        """Test empty description."""
        is_valid, msg = validate_request_description("")
        assert is_valid is False
        assert "empty" in msg.lower()

    def test_too_short_description(self) -> None:
        """Test too short description."""
        is_valid, msg = validate_request_description("123456789")
        assert is_valid is False
        assert "10" in msg

    def test_too_long_description(self) -> None:
        """Test too long description."""
        long_desc = "A" * 1001
        is_valid, msg = validate_request_description(long_desc)
        assert is_valid is False
        assert "1000" in msg

    def test_boundary_description_min(self) -> None:
        """Test minimum valid description."""
        is_valid, msg = validate_request_description("1234567890")
        assert is_valid is True

    def test_boundary_description_max(self) -> None:
        """Test maximum valid description."""
        is_valid, msg = validate_request_description("A" * 1000)
        assert is_valid is True


class TestValidateLocation:
    """Test location validation."""

    def test_valid_location(self) -> None:
        """Test valid location."""
        is_valid, msg = validate_location("Room 101")
        assert is_valid is True
        assert msg == ""

    def test_empty_location(self) -> None:
        """Test empty location."""
        is_valid, msg = validate_location("")
        assert is_valid is False
        assert "empty" in msg.lower()

    def test_too_short_location(self) -> None:
        """Test too short location."""
        is_valid, msg = validate_location("ab")
        assert is_valid is False

    def test_too_long_location(self) -> None:
        """Test too long location."""
        long_location = "A" * 101
        is_valid, msg = validate_location(long_location)
        assert is_valid is False


class TestValidateComment:
    """Test comment validation."""

    def test_valid_comment(self) -> None:
        """Test valid comment."""
        is_valid, msg = validate_comment("Will fix it ASAP")
        assert is_valid is True
        assert msg == ""

    def test_empty_comment(self) -> None:
        """Test empty comment."""
        is_valid, msg = validate_comment("")
        assert is_valid is False
        assert "empty" in msg.lower()

    def test_too_long_comment(self) -> None:
        """Test too long comment."""
        long_comment = "A" * 501
        is_valid, msg = validate_comment(long_comment)
        assert is_valid is False
        assert "500" in msg

    def test_boundary_comment_max(self) -> None:
        """Test maximum valid comment."""
        is_valid, msg = validate_comment("A" * 500)
        assert is_valid is True


class TestSanitizeText:
    """Test text sanitization."""

    def test_clean_text(self) -> None:
        """Test clean text."""
        result = sanitize_text("hello world")
        assert result == "hello world"

    def test_extra_whitespace(self) -> None:
        """Test removal of extra whitespace."""
        result = sanitize_text("  many    spaces  ")
        assert result == "many spaces"

    def test_multiple_newlines(self) -> None:
        """Test removal of multiple newlines."""
        result = sanitize_text("line1\n\n\nline2")
        assert result == "line1 line2"

    def test_length_limit(self) -> None:
        """Test length limiting."""
        long_text = "A" * 10001
        result = sanitize_text(long_text)
        assert len(result) == 10003  # 10000 + "..."
        assert result.endswith("...")

    def test_empty_text(self) -> None:
        """Test empty text."""
        result = sanitize_text("")
        assert result == ""

    def test_none_text(self) -> None:
        """Test None text."""
        result = sanitize_text("")
        assert result == ""


class TestRateLimiter:
    """Test rate limiter."""

    def test_rate_limiter_allows_first_requests(self) -> None:
        """Test that first requests are allowed."""
        limiter = RateLimiter()
        user_id = 123

        for _ in range(5):
            assert limiter.is_allowed(user_id, "test", max_requests=5, time_window=60) is True

    def test_rate_limiter_blocks_excess_requests(self) -> None:
        """Test that excess requests are blocked."""
        limiter = RateLimiter()
        user_id = 123

        for _ in range(5):
            limiter.is_allowed(user_id, "test", max_requests=5, time_window=60)

        # 6th request should be blocked
        assert limiter.is_allowed(user_id, "test", max_requests=5, time_window=60) is False

    def test_rate_limiter_different_actions(self) -> None:
        """Test that different actions have separate limits."""
        limiter = RateLimiter()
        user_id = 123

        # Fill up action1
        for _ in range(5):
            limiter.is_allowed(user_id, "action1", max_requests=5, time_window=60)

        # action1 should be blocked
        assert limiter.is_allowed(user_id, "action1", max_requests=5, time_window=60) is False

        # action2 should still work
        assert limiter.is_allowed(user_id, "action2", max_requests=5, time_window=60) is True

    def test_rate_limiter_different_users(self) -> None:
        """Test that different users have separate limits."""
        limiter = RateLimiter()

        # Fill up user1
        for _ in range(5):
            limiter.is_allowed(111, "test", max_requests=5, time_window=60)

        # user1 should be blocked
        assert limiter.is_allowed(111, "test", max_requests=5, time_window=60) is False

        # user2 should still work
        assert limiter.is_allowed(222, "test", max_requests=5, time_window=60) is True