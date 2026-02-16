"""Authentication API endpoints."""

from datetime import UTC, datetime, timedelta
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Request, status
from jose import jwt
from passlib.context import CryptContext
from pydantic import BaseModel, EmailStr
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.auth import CurrentUser
from app.core.config import settings
from app.core.limiter import limiter
from app.db.session import get_db
from app.models.organization import Organization
from app.models.project import Project
from app.models.unit import Unit
from app.models.department import Department
from app.models.user import AuthProvider, User, UserRole
from app.models.workspace import Workspace

router = APIRouter(prefix="/auth", tags=["Authentication"])
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


# === Schemas ===

class RegisterRequest(BaseModel):
    email: EmailStr
    password: str
    full_name: str
    organization_name: str | None = None


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    user: dict[str, Any]


class SSOLoginRequest(BaseModel):
    """SSO login with Azure AD token."""
    id_token: str
    provider: str = "azure_ad"


# === Utilities ===

def create_access_token(user_id: int, expires_delta: timedelta | None = None) -> str:
    """Create JWT access token."""
    expire = datetime.now(UTC) + (expires_delta or timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES))
    payload = {"sub": str(user_id), "exp": expire, "type": "access"}
    return jwt.encode(payload, settings.SECRET_KEY, algorithm=settings.ALGORITHM)


def create_refresh_token(user_id: int) -> str:
    """Create JWT refresh token."""
    expire = datetime.now(UTC) + timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)
    payload = {"sub": str(user_id), "exp": expire, "type": "refresh"}
    return jwt.encode(payload, settings.SECRET_KEY, algorithm=settings.ALGORITHM)


def hash_password(password: str) -> str:
    """Hash a password."""
    return pwd_context.hash(password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a password against its hash."""
    return pwd_context.verify(plain_password, hashed_password)


def _user_to_dict(user: User) -> dict[str, Any]:
    """Convert user to response dict."""
    return {
        "id": user.id,
        "email": user.email,
        "full_name": user.full_name,
        "role": user.role.value if hasattr(user.role, "value") else user.role,
        "provider": user.provider.value if hasattr(user.provider, "value") else user.provider,
        "organization_id": str(user.organization_id) if user.organization_id else None,
        "email_verified": user.email_verified,
        "is_active": user.is_active,
        "department": user.department,
        "job_title": user.job_title,
    }


# === Endpoints ===

@router.post("/register", response_model=TokenResponse, status_code=status.HTTP_201_CREATED)
@limiter.limit("5/minute")
async def register(
    data: RegisterRequest,
    request: Request,
    db: AsyncSession = Depends(get_db),
) -> TokenResponse:
    """Register a new user with optional organization creation."""
    # Check existing user
    result = await db.execute(select(User).where(User.email == data.email))
    if result.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered",
        )

    # Create user
    user = User(
        email=data.email,
        hashed_password=hash_password(data.password),
        full_name=data.full_name,
        provider=AuthProvider.EMAIL,
        role=UserRole.ORG_ADMIN,
        email_verified=not settings.EMAIL_VERIFICATION_REQUIRED,
    )
    db.add(user)
    await db.flush()

    # Create organization if name provided
    if data.organization_name:
        slug = data.organization_name.lower().replace(" ", "-")[:100]
        org = Organization(
            name=data.organization_name,
            slug=slug,
            owner_id=user.id,
        )
        db.add(org)
        await db.flush()

        user.organization_id = org.id

        # Create default hierarchy: Unit > Department > Project > Workspace
        unit = Unit(
            organization_id=org.id,
            name="Default Unit",
            slug="default-unit",
        )
        db.add(unit)
        await db.flush()

        dept = Department(
            unit_id=unit.id,
            organization_id=org.id,
            name="Default Department",
            slug="default-department",
        )
        db.add(dept)
        await db.flush()

        project = Project(
            department_id=dept.id,
            organization_id=org.id,
            name="Default Project",
            slug="default-project",
        )
        db.add(project)
        await db.flush()

        workspace = Workspace(
            project_id=project.id,
            organization_id=org.id,
            name="Default Workspace",
            is_default=True,
        )
        db.add(workspace)

    # Generate tokens
    access_token = create_access_token(user.id)
    refresh_token = create_refresh_token(user.id)

    return TokenResponse(
        access_token=access_token,
        refresh_token=refresh_token,
        user=_user_to_dict(user),
    )


@router.post("/login", response_model=TokenResponse)
@limiter.limit("10/minute")
async def login(
    data: LoginRequest,
    request: Request,
    db: AsyncSession = Depends(get_db),
) -> TokenResponse:
    """Login with email and password."""
    result = await db.execute(select(User).where(User.email == data.email))
    user = result.scalar_one_or_none()

    if not user or not user.hashed_password:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid credentials",
        )

    if user.is_account_locked():
        raise HTTPException(
            status_code=status.HTTP_423_LOCKED,
            detail="Account is locked. Please try again later.",
        )

    if not verify_password(data.password, user.hashed_password):
        user.failed_login_attempts += 1
        if user.failed_login_attempts >= 5:
            user.locked_until = datetime.now(UTC) + timedelta(minutes=15)
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid credentials",
        )

    # Reset on successful login
    user.failed_login_attempts = 0
    user.locked_until = None
    user.last_login_at = datetime.now(UTC)

    access_token = create_access_token(user.id)
    refresh_token = create_refresh_token(user.id)

    return TokenResponse(
        access_token=access_token,
        refresh_token=refresh_token,
        user=_user_to_dict(user),
    )


@router.get("/me")
async def get_current_user_info(current_user: CurrentUser) -> dict[str, Any]:
    """Get current authenticated user info."""
    return _user_to_dict(current_user)


@router.post("/logout")
async def logout(current_user: CurrentUser) -> dict[str, str]:
    """Logout current session."""
    return {"message": "Successfully logged out"}
