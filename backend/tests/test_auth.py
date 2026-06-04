"""Tests for auth service - rate limiting, password hashing, token management."""

import time

import pytest

from app.services.auth_service import (
    hash_password,
    verify_password,
    create_access_token,
    decode_access_token,
    signup,
    login,
    update_profile,
    check_login_rate_limit,
    reset_login_rate_limit,
    generate_reset_token,
    reset_password,
    LOGIN_ATTEMPTS,
)
from app.config import settings


class TestPasswordHashing:
    def test_hash_and_verify(self):
        password = "my_secret_password_123"
        hashed = hash_password(password)
        assert hashed != password
        assert verify_password(password, hashed)

    def test_wrong_password_fails(self):
        hashed = hash_password("correct_password")
        assert not verify_password("wrong_password", hashed)

    def test_hash_is_unique(self):
        h1 = hash_password("same_password")
        h2 = hash_password("same_password")
        assert h1 != h2

    def test_bcrypt_rounds(self):
        hashed = hash_password("test")
        assert hashed.startswith("$2b$12$") or hashed.startswith("$2a$12$")


class TestTokenManagement:
    def test_create_and_decode(self):
        token = create_access_token("user_123")
        assert token is not None
        user_id = decode_access_token(token)
        assert user_id == "user_123"

    def test_invalid_token_returns_none(self):
        assert decode_access_token("invalid_token_here") is None

    def test_tampered_token_returns_none(self):
        token = create_access_token("user_123")
        tampered = token[:-5] + "XXXXX"
        assert decode_access_token(tampered) is None


class TestRateLimiting:
    def setup_method(self):
        LOGIN_ATTEMPTS.clear()

    def test_allows_within_limit(self):
        identifier = "test_ip"
        for _ in range(4):
            check_login_rate_limit(identifier)
        assert len(LOGIN_ATTEMPTS[identifier]) == 4

    def test_blocks_after_limit(self):
        identifier = "test_ip_2"
        for _ in range(5):
            check_login_rate_limit(identifier)
        with pytest.raises(RuntimeError, match="Too many login attempts"):
            check_login_rate_limit(identifier)

    def test_reset_clears_attempts(self):
        identifier = "test_ip_3"
        for _ in range(5):
            check_login_rate_limit(identifier)
        reset_login_rate_limit(identifier)
        assert identifier not in LOGIN_ATTEMPTS
        check_login_rate_limit(identifier)

    def test_different_ips_independent(self):
        for _ in range(5):
            check_login_rate_limit("ip_1")
        check_login_rate_limit("ip_2")
        with pytest.raises(RuntimeError):
            check_login_rate_limit("ip_1")
        check_login_rate_limit("ip_2")


class TestProfileUpdate:
    _email_counter = 0

    def _unique_email(self, prefix="profile_test"):
        TestProfileUpdate._email_counter += 1
        return f"{prefix}_{TestProfileUpdate._email_counter}_{time.time_ns()}@example.com"

    def test_update_full_name(self):
        email = self._unique_email()
        result = signup(email, "pass123", "Old Name")
        assert result is not None
        updated = update_profile(result["user_id"], full_name="New Name")
        assert updated["full_name"] == "New Name"
        assert updated["email"] == email

    def test_update_email(self):
        email = self._unique_email()
        new_email = self._unique_email("new_email")
        result = signup(email, "pass123", "Test User")
        assert result is not None
        updated = update_profile(result["user_id"], email=new_email)
        assert updated["email"] == new_email

    def test_email_uniqueness(self):
        existing_email = self._unique_email("existing")
        signup(existing_email, "pass123", "User A")
        dup_email = self._unique_email("dup")
        result = signup(dup_email, "pass123", "User B")
        assert result is not None
        with pytest.raises(ValueError, match="Email already in use"):
            update_profile(result["user_id"], email=existing_email)

    def test_update_password(self):
        email = self._unique_email("pw")
        result = signup(email, "old_pass", "Test User")
        assert result is not None
        updated = update_profile(
            result["user_id"],
            current_password="old_pass",
            new_password="new_pass",
        )
        assert updated is not None
        login_result = login(email, "new_pass")
        assert login_result is not None

    def test_update_password_wrong_current(self):
        email = self._unique_email("wrong_pw")
        result = signup(email, "correct_pass", "Test User")
        assert result is not None
        with pytest.raises(ValueError, match="Current password is incorrect"):
            update_profile(
                result["user_id"],
                current_password="wrong_pass",
                new_password="new_pass",
            )

    def test_update_nonexistent_user(self):
        with pytest.raises(ValueError, match="User not found"):
            update_profile("nonexistent_user")


class TestForgotPassword:
    _email_counter = 0

    def _unique_email(self, prefix="reset_test"):
        TestForgotPassword._email_counter += 1
        return f"{prefix}_{TestForgotPassword._email_counter}_{time.time_ns()}@example.com"

    def test_generate_reset_token_for_valid_email(self):
        email = self._unique_email()
        result = signup(email, "pass123", "Test User")
        assert result is not None
        token = generate_reset_token(email)
        assert token is not None
        assert len(token) > 20

    def test_generate_reset_token_invalid_email(self):
        token = generate_reset_token("nonexistent@example.com")
        assert token is None

    def test_reset_password_with_valid_token(self):
        email = self._unique_email()
        result = signup(email, "old_pass", "Test User")
        assert result is not None
        token = generate_reset_token(email)
        assert token is not None
        success = reset_password(token, "new_password_123")
        assert success
        login_result = login(email, "new_password_123")
        assert login_result is not None

    def test_reset_password_with_invalid_token(self):
        success = reset_password("invalid_token_here", "new_pass")
        assert not success

    def test_reset_token_expires(self):
        import datetime
        email = self._unique_email()
        result = signup(email, "pass123", "Test User")
        assert result is not None
        token = generate_reset_token(email)
        assert token is not None
        from app.services.auth_service import _load_users
        users = _load_users()
        for uid, user in users.items():
            if user["email"] == email:
                user["reset_token_expires"] = (datetime.datetime.now(datetime.timezone.utc) - datetime.timedelta(hours=2)).isoformat()
                from app.json_storage import locked_write
                from app.services.auth_service import USERS_FILE
                locked_write(USERS_FILE, users)
                break
        success = reset_password(token, "new_pass")
        assert not success
