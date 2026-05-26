from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Cookie, Depends, HTTPException, Response, status
from pydantic import BaseModel, Field
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import Settings, get_settings
from app.db.session import get_db
from app.services.auth import AuthService

router = APIRouter(prefix="/v1/auth", tags=["auth"])


class RegisterRequest(BaseModel):
    email: str = Field(pattern=r"^[^@\s]+@[^@\s]+\.[^@\s]+$")
    password: str = Field(min_length=8, max_length=128)
    display_name: str = Field(min_length=1, max_length=80)
    locale: str = "pt-BR"
    accept_terms: bool


class RegisterResponse(BaseModel):
    user_id: UUID
    email_verification_required: bool


class LoginRequest(BaseModel):
    email: str = Field(pattern=r"^[^@\s]+@[^@\s]+\.[^@\s]+$")
    password: str


class UserDTO(BaseModel):
    id: UUID
    email: str
    display_name: str
    plan: str


class LoginResponse(BaseModel):
    user: UserDTO


@router.post("/register", response_model=RegisterResponse, status_code=status.HTTP_201_CREATED)
async def register(
    payload: RegisterRequest,
    db: Annotated[AsyncSession, Depends(get_db)],
    settings: Annotated[Settings, Depends(get_settings)],
) -> RegisterResponse:
    if not payload.accept_terms:
        raise HTTPException(status_code=422, detail="Terms must be accepted")
    service = AuthService(db, settings)
    try:
        user_id = await service.register(
            payload.email,
            payload.password,
            payload.display_name,
            payload.locale,
        )
    except IntegrityError as exc:
        await db.rollback()
        raise HTTPException(status_code=409, detail="Email already in use") from exc
    return RegisterResponse(user_id=user_id, email_verification_required=True)


@router.post("/login", response_model=LoginResponse)
async def login(
    payload: LoginRequest,
    response: Response,
    db: Annotated[AsyncSession, Depends(get_db)],
    settings: Annotated[Settings, Depends(get_settings)],
) -> LoginResponse:
    result = await AuthService(db, settings).login(payload.email, payload.password)
    if result is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials")
    user, access, refresh = result
    _set_auth_cookies(response, access, refresh, settings)
    return LoginResponse(user=UserDTO.model_validate(user))


@router.post("/refresh")
async def refresh(
    response: Response,
    db: Annotated[AsyncSession, Depends(get_db)],
    settings: Annotated[Settings, Depends(get_settings)],
    pi_refresh: Annotated[str | None, Cookie()] = None,
) -> dict[str, str]:
    if not pi_refresh:
        raise HTTPException(status_code=401, detail="Missing refresh token")
    result = await AuthService(db, settings).refresh(pi_refresh)
    if result is None:
        raise HTTPException(status_code=401, detail="Invalid refresh token")
    access, refresh_token = result
    _set_auth_cookies(response, access, refresh_token, settings)
    return {"status": "ok"}


@router.post("/logout", status_code=status.HTTP_204_NO_CONTENT)
async def logout(
    response: Response,
    db: Annotated[AsyncSession, Depends(get_db)],
    settings: Annotated[Settings, Depends(get_settings)],
    pi_refresh: Annotated[str | None, Cookie()] = None,
) -> None:
    await AuthService(db, settings).logout(pi_refresh)
    response.delete_cookie("pi_access", path="/")
    response.delete_cookie("pi_refresh", path="/v1/auth/refresh")


@router.post("/verify-email")
async def verify_email() -> dict[str, str]:
    return {"status": "ok"}


@router.post("/forgot-password", status_code=status.HTTP_204_NO_CONTENT)
async def forgot_password() -> None:
    return None


@router.post("/reset-password")
async def reset_password() -> dict[str, str]:
    return {"status": "ok"}


def _set_auth_cookies(response: Response, access: str, refresh: str, settings: Settings) -> None:
    secure = settings.is_production
    response.set_cookie("pi_access", access, httponly=True, secure=secure, samesite="lax", path="/")
    response.set_cookie(
        "pi_refresh",
        refresh,
        httponly=True,
        secure=secure,
        samesite="lax",
        path="/v1/auth/refresh",
    )
