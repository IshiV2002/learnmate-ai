from app.database.models import UserRecord


def make_test_user(user_id: str = "test-user") -> UserRecord:
    """Create a safe in-memory identity for non-authentication API tests."""
    return UserRecord(
        user_id=user_id,
        full_name="Test Student",
        email=f"{user_id}@example.com",
        password_hash="not-used-by-overridden-authentication",
        created_at="2026-01-01T00:00:00+00:00",
    )
