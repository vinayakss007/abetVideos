"""Auth service - user registration, login, and JWT token management."""

import json
import logging
import time
from collections import defaultdict
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any

import bcrypt
import secrets
from jose import JWTError, jwt

from app.config import settings
from app.json_storage import locked_read, locked_write

logger = logging.getLogger(__name__)

USERS_FILE = Path(__file__).parent.parent / "data" / "users.json"
_OLD_USERS_FILE = Path(__file__).parent.parent / "users.json"

# Migrate from old location if exists
if _OLD_USERS_FILE.exists():
    try:
        data = json.loads(_OLD_USERS_FILE.read_text())
        USERS_FILE.parent.mkdir(parents=True, exist_ok=True)
        locked_write(USERS_FILE, data)
        _OLD_USERS_FILE.rename(_OLD_USERS_FILE.with_suffix(".json.bak"))
        logger.info("Migrated users.json to %s", USERS_FILE)
    except (json.JSONDecodeError, OSError) as e:
        logger.warning("Failed to migrate users.json: %s", e)


# Simple in-memory rate limiter for login attempts
LOGIN_ATTEMPTS: dict[str, list[float]] = defaultdict(list)
MAX_LOGIN_ATTEMPTS = 5
LOGIN_WINDOW_SECONDS = 300


def check_login_rate_limit(identifier: str) -> None:
    """Check if the IP/email has exceeded login attempt limits. Raises RuntimeError if blocked."""
    now = time.time()
    window_start = now - LOGIN_WINDOW_SECONDS
    attempts = [t for t in LOGIN_ATTEMPTS[identifier] if t > window_start]
    LOGIN_ATTEMPTS[identifier] = attempts
    if len(attempts) >= MAX_LOGIN_ATTEMPTS:
        raise RuntimeError("Too many login attempts. Try again in 5 minutes.")
    LOGIN_ATTEMPTS[identifier].append(now)


def reset_login_rate_limit(identifier: str) -> None:
    """Clear login attempts on successful login."""
    LOGIN_ATTEMPTS.pop(identifier, None)


def _load_users() -> dict[str, Any]:
    return locked_read(USERS_FILE)


def _save_users(data: dict[str, Any]) -> None:
    locked_write(USERS_FILE, data)


def hash_password(password: str) -> str:
    return bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt(rounds=12)).decode("utf-8")


def verify_password(plain_password: str, hashed_password: str) -> bool:
    return bcrypt.checkpw(
        plain_password.encode("utf-8"), hashed_password.encode("utf-8")
    )


def create_access_token(user_id: str) -> str:
    expire = datetime.now(timezone.utc) + timedelta(minutes=settings.jwt_expire_minutes)
    to_encode = {"sub": user_id, "exp": expire}
    return jwt.encode(to_encode, settings.jwt_secret, algorithm=settings.jwt_algorithm)


def decode_access_token(token: str) -> str | None:
    try:
        payload = jwt.decode(token, settings.jwt_secret, algorithms=[settings.jwt_algorithm])
        user_id: str = payload.get("sub")
        if user_id is None:
            return None
        return user_id
    except JWTError:
        return None


def signup(email: str, password: str, full_name: str) -> dict[str, Any] | None:
    users = _load_users()
    if any(u["email"] == email for u in users.values()):
        return None

    user_id = f"user_{len(users) + 1}_{datetime.now(timezone.utc).strftime('%Y%m%d%H%M%S')}"
    hashed_pw = hash_password(password)

    users[user_id] = {
        "user_id": user_id,
        "email": email,
        "password_hash": hashed_pw,
        "full_name": full_name,
        "created_at": datetime.now(timezone.utc).isoformat(),
    }
    _save_users(users)

    token = create_access_token(user_id)

    return {
        "user_id": user_id,
        "email": email,
        "full_name": full_name,
        "token": token,
    }


def login(email: str, password: str, ip_address: str = "") -> dict[str, Any] | None:
    identifier = ip_address or email
    check_login_rate_limit(identifier)
    users = _load_users()
    for user_id, user in users.items():
        if user["email"] == email and verify_password(password, user["password_hash"]):
            reset_login_rate_limit(identifier)
            token = create_access_token(user_id)
            return {
                "user_id": user_id,
                "email": user["email"],
                "full_name": user["full_name"],
                "token": token,
            }
    return None


def get_user_by_id(user_id: str) -> dict[str, Any] | None:
    users = _load_users()
    user = users.get(user_id)
    if user:
        return {
            "user_id": user["user_id"],
            "email": user["email"],
            "full_name": user["full_name"],
            "created_at": user["created_at"],
        }
    return None


def generate_reset_token(email: str) -> str | None:
    """Generate a password reset token for the given email. Returns None if email not found."""
    users = _load_users()
    for user_id, user in users.items():
        if user["email"] == email:
            token = secrets.token_urlsafe(32)
            user["reset_token"] = token
            user["reset_token_expires"] = (datetime.now(timezone.utc) + timedelta(hours=1)).isoformat()
            _save_users(users)
            return token
    return None


def reset_password(token: str, new_password: str) -> bool:
    """Reset a user's password using a valid reset token. Returns False if token invalid/expired."""
    users = _load_users()
    now = datetime.now(timezone.utc)
    for user_id, user in users.items():
        reset_token = user.get("reset_token")
        expires_str = user.get("reset_token_expires")
        if reset_token and reset_token == token and expires_str:
            try:
                expires = datetime.fromisoformat(expires_str)
                if now < expires:
                    user["password_hash"] = hash_password(new_password)
                    user.pop("reset_token", None)
                    user.pop("reset_token_expires", None)
                    _save_users(users)
                    return True
            except (ValueError, TypeError):
                pass
    return False


def update_profile(
    user_id: str,
    email: str | None = None,
    full_name: str | None = None,
    current_password: str | None = None,
    new_password: str | None = None,
) -> dict[str, Any]:
    users = _load_users()
    user = users.get(user_id)
    if not user:
        raise ValueError("User not found")

    if email is not None:
        if any(u["email"] == email and uid != user_id for uid, u in users.items()):
            raise ValueError("Email already in use")
        user["email"] = email

    if full_name is not None:
        user["full_name"] = full_name

    if new_password is not None:
        if not current_password or not verify_password(current_password, user["password_hash"]):
            raise ValueError("Current password is incorrect")
        user["password_hash"] = hash_password(new_password)

    _save_users(users)
    return {
        "user_id": user["user_id"],
        "email": user["email"],
        "full_name": user["full_name"],
        "created_at": user["created_at"],
    }
