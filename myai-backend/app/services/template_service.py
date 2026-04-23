from __future__ import annotations

from sqlalchemy import and_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models.resume_template import ResumeTemplateVersion
from app.schemas.templates import ResumeTemplateDefinition
from app.services.template_fallbacks import fallback_templates


def _fallback_template(
    *,
    template_id: str,
    template_version: str | None,
) -> ResumeTemplateDefinition | None:
    for template in fallback_templates():
        if template.template_id != template_id:
            continue
        if template_version and template.template_version != template_version:
            continue
        return template
    return None


async def get_template_definition(
    session: AsyncSession | None,
    *,
    template_id: str,
    template_version: str | None,
) -> ResumeTemplateDefinition | None:
    if session is not None:
        try:
            if template_version:
                result = await session.execute(
                    select(ResumeTemplateVersion)
                    .where(
                        and_(
                            ResumeTemplateVersion.template_id == template_id,
                            ResumeTemplateVersion.template_version == template_version,
                            ResumeTemplateVersion.is_published.is_(True),
                        )
                    )
                    .limit(1)
                )
                row = result.scalar_one_or_none()
                if row:
                    template = ResumeTemplateDefinition.model_validate(row.definition)
                    return template.model_copy(
                        update={"is_published": row.is_published, "published_at": row.published_at}
                    )
            else:
                result = await session.execute(
                    select(ResumeTemplateVersion)
                    .where(
                        and_(
                            ResumeTemplateVersion.template_id == template_id,
                            ResumeTemplateVersion.is_published.is_(True),
                        )
                    )
                    .order_by(ResumeTemplateVersion.published_at.desc().nullslast())
                    .limit(1)
                )
                row = result.scalar_one_or_none()
                if row:
                    template = ResumeTemplateDefinition.model_validate(row.definition)
                    return template.model_copy(
                        update={"is_published": row.is_published, "published_at": row.published_at}
                    )
        except Exception:
            pass

    return _fallback_template(template_id=template_id, template_version=template_version)


async def list_latest_published_templates(session: AsyncSession | None) -> list[ResumeTemplateDefinition]:
    if session is not None:
        try:
            result = await session.execute(
                select(ResumeTemplateVersion)
                .where(ResumeTemplateVersion.is_published.is_(True))
                .order_by(
                    ResumeTemplateVersion.template_id.asc(),
                    ResumeTemplateVersion.published_at.desc().nullslast(),
                )
            )
            versions = list(result.scalars().all())
            latest: dict[str, ResumeTemplateVersion] = {}
            for version in versions:
                if version.template_id not in latest:
                    latest[version.template_id] = version

            templates: list[ResumeTemplateDefinition] = []
            for version in latest.values():
                template = ResumeTemplateDefinition.model_validate(version.definition)
                templates.append(
                    template.model_copy(
                        update={"is_published": version.is_published, "published_at": version.published_at}
                    )
                )
            if templates:
                return templates
        except Exception:
            pass

    return sorted(fallback_templates(), key=lambda item: item.display_name.lower())
