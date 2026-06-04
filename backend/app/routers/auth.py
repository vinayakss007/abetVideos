"""Authentication API routes - signup, login, logout, and user info."""

import logging

from fastapi import APIRouter, HTTPException, Depends, Request, Response
from pydantic import BaseModel

from app.auth.dependencies import get_current_user
from app.models.schemas import LoginRequest, SignupRequest, ProfileUpdateRequest, UserResponse
from app.services.auth_service import signup, login, update_profile, generate_reset_token, reset_password

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/auth", tags=["auth"])


class ForgotPasswordRequest(BaseModel):
    email: str


class ResetPasswordRequest(BaseModel):
    token: str
    new_password: str

COOKIE_NAME = "abet_token"
COOKIE_MAX_AGE = 7 * 24 * 60 * 60  # 7 days


def _set_auth_cookie(response: Response, token: str) -> None:
    response.set_cookie(
        key=COOKIE_NAME,
        value=token,
        max_age=COOKIE_MAX_AGE,
        httponly=True,
        samesite="lax",
        secure=False,
    )


def _clear_auth_cookie(response: Response) -> None:
    response.delete_cookie(key=COOKIE_NAME)


@router.post("/signup")
async def signup_user(request: SignupRequest, response: Response):
    result = signup(request.email, request.password, request.full_name)
    if result is None:
        raise HTTPException(status_code=409, detail="Email already registered")
    _set_auth_cookie(response, result["token"])
    return result


@router.post("/login")
async def login_user(request: LoginRequest, req: Request, response: Response):
    ip_address = req.client.host if req.client else ""
    try:
        result = login(request.email, request.password, ip_address=ip_address)
    except RuntimeError as e:
        raise HTTPException(status_code=429, detail=str(e))
    if result is None:
        raise HTTPException(status_code=401, detail="Invalid email or password")
    _set_auth_cookie(response, result["token"])
    return result


@router.post("/logout")
async def logout_user(response: Response):
    _clear_auth_cookie(response)
    return {"detail": "Logged out"}


@router.get("/me", response_model=UserResponse)
async def get_me(current_user: dict = Depends(get_current_user)):
    return current_user


@router.post("/forgot-password")
async def forgot_password(request: ForgotPasswordRequest):
    """Request a password reset token."""
    token = generate_reset_token(request.email)
    if token is None:
        return {"detail": "If the email exists, a reset link has been sent"}
    logger.info("Password reset token generated for %s: %s", request.email, token)
    return {"detail": "If the email exists, a reset link has been sent", "reset_token": token}


@router.post("/reset-password")
async def reset_password_endpoint(request: ResetPasswordRequest):
    """Reset password using a valid reset token."""
    if len(request.new_password) < 6:
        raise HTTPException(status_code=400, detail="Password must be at least 6 characters")
    success = reset_password(request.token, request.new_password)
    if not success:
        raise HTTPException(status_code=400, detail="Invalid or expired reset token")
    return {"detail": "Password reset successfully"}


@router.put("/profile", response_model=UserResponse)
async def update_user_profile(
    request: ProfileUpdateRequest,
    current_user: dict = Depends(get_current_user),
):
    try:
        result = update_profile(
            user_id=current_user["user_id"],
            email=request.email,
            full_name=request.full_name,
            current_password=request.current_password,
            new_password=request.new_password,
        )
        return result
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
