from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import optional_db_session
from app.schemas.templates import ResumeTemplateDefinition
from app.services.template_service import get_template_definition, list_latest_published_templates

router = APIRouter()


@router.get("/templates", response_model=list[ResumeTemplateDefinition])
async def list_templates(
    session: AsyncSession | None = Depends(optional_db_session),
) -> list[ResumeTemplateDefinition]:
    return await list_latest_published_templates(session)


@router.get("/templates/{template_id}", response_model=ResumeTemplateDefinition)
async def get_template(
    template_id: str,
    version: str | None = None,
    session: AsyncSession | None = Depends(optional_db_session),
) -> ResumeTemplateDefinition:
    definition = await get_template_definition(
        session,
        template_id=template_id,
        template_version=version,
    )
    if definition is None:
        raise HTTPException(status_code=404, detail="Template not found")
    return definition

