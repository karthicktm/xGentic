"""Contact API endpoints — CRUD for enterprise CRM contacts."""

from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.auth import CurrentUser
from app.db.session import get_db
from app.models.contact import Contact

router = APIRouter(prefix="/contacts", tags=["Contacts"])


class ContactCreate(BaseModel):
    first_name: str
    last_name: str | None = None
    email: str | None = None
    phone_number: str | None = None
    company_name: str | None = None
    department: str | None = None
    job_title: str | None = None
    status: str = "new"
    tags: list[str] | None = None


class ContactUpdate(BaseModel):
    first_name: str | None = None
    last_name: str | None = None
    email: str | None = None
    phone_number: str | None = None
    company_name: str | None = None
    department: str | None = None
    job_title: str | None = None
    status: str | None = None
    tags: list[str] | None = None


def _contact_to_dict(contact: Contact) -> dict[str, Any]:
    return {
        "id": contact.id,
        "user_id": contact.user_id,
        "workspace_id": str(contact.workspace_id) if contact.workspace_id else None,
        "organization_id": str(contact.organization_id) if contact.organization_id else None,
        "first_name": contact.first_name,
        "last_name": contact.last_name,
        "email": contact.email,
        "phone_number": contact.phone_number,
        "company_name": contact.company_name,
        "department": contact.department,
        "job_title": contact.job_title,
        "manager": contact.manager,
        "status": contact.status,
        "tags": contact.tags,
        "notes": contact.notes,
        "custom_fields": contact.custom_fields,
        "created_at": contact.created_at.isoformat(),
        "updated_at": contact.updated_at.isoformat(),
    }


@router.get("")
async def list_contacts(
    current_user: CurrentUser,
    limit: int = Query(50, le=100),
    offset: int = Query(0),
    db: AsyncSession = Depends(get_db),
) -> list[dict[str, Any]]:
    """List contacts for the current user."""
    query = (
        select(Contact)
        .where(Contact.user_id == current_user.id)
        .order_by(Contact.created_at.desc())
        .limit(limit)
        .offset(offset)
    )
    result = await db.execute(query)
    return [_contact_to_dict(c) for c in result.scalars().all()]


@router.get("/{contact_id}")
async def get_contact(
    contact_id: int,
    current_user: CurrentUser,
    db: AsyncSession = Depends(get_db),
) -> dict[str, Any]:
    """Get contact details."""
    result = await db.execute(
        select(Contact).where(
            Contact.id == contact_id, Contact.user_id == current_user.id
        )
    )
    contact = result.scalar_one_or_none()
    if not contact:
        raise HTTPException(status_code=404, detail="Contact not found")
    return _contact_to_dict(contact)


@router.post("", status_code=status.HTTP_201_CREATED)
async def create_contact(
    data: ContactCreate,
    current_user: CurrentUser,
    db: AsyncSession = Depends(get_db),
) -> dict[str, Any]:
    """Create a new contact."""
    contact = Contact(
        user_id=current_user.id,
        organization_id=current_user.organization_id,
        first_name=data.first_name,
        last_name=data.last_name,
        email=data.email,
        phone_number=data.phone_number,
        company_name=data.company_name,
        department=data.department,
        job_title=data.job_title,
        status=data.status,
        tags=data.tags or [],
    )
    db.add(contact)
    await db.flush()
    return _contact_to_dict(contact)


@router.patch("/{contact_id}")
async def update_contact(
    contact_id: int,
    data: ContactUpdate,
    current_user: CurrentUser,
    db: AsyncSession = Depends(get_db),
) -> dict[str, Any]:
    """Update a contact."""
    result = await db.execute(
        select(Contact).where(
            Contact.id == contact_id, Contact.user_id == current_user.id
        )
    )
    contact = result.scalar_one_or_none()
    if not contact:
        raise HTTPException(status_code=404, detail="Contact not found")

    for key, value in data.model_dump(exclude_unset=True).items():
        setattr(contact, key, value)

    await db.flush()
    return _contact_to_dict(contact)


@router.delete("/{contact_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_contact(
    contact_id: int,
    current_user: CurrentUser,
    db: AsyncSession = Depends(get_db),
) -> None:
    """Delete a contact."""
    result = await db.execute(
        select(Contact).where(
            Contact.id == contact_id, Contact.user_id == current_user.id
        )
    )
    contact = result.scalar_one_or_none()
    if not contact:
        raise HTTPException(status_code=404, detail="Contact not found")

    await db.delete(contact)
    await db.flush()
