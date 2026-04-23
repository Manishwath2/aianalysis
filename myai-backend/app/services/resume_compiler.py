from __future__ import annotations

from datetime import datetime

from app.schemas.candidate import CandidateProfile
from app.schemas.resume import (
    BulletsBlock,
    ResumeDocument,
    ResumeSection,
    TagBlock,
    TextBlock,
    TimelineBlock,
    TimelineItem,
)
from app.utils.ids import new_uuid


def compile_resume(*, candidate: CandidateProfile, template_id: str, locale: str) -> ResumeDocument:
    sections: list[ResumeSection] = []

    header_text = candidate.personal.full_name
    if candidate.personal.headline:
        header_text += f" - {candidate.personal.headline}"
    sections.append(
        ResumeSection(
            type="header",
            title=None,
            blocks=[TextBlock(text=header_text)],
        )
    )

    if candidate.summary and candidate.summary.about:
        blocks = [TextBlock(text=candidate.summary.about)]
        if candidate.summary.highlights:
            blocks.append(BulletsBlock(items=candidate.summary.highlights))
        sections.append(ResumeSection(type="summary", title="Summary", blocks=blocks))

    if candidate.skills:
        skill_lines: list[str] = []
        for group in candidate.skills:
            names = [item.name for item in group.items if item.name]
            if names:
                skill_lines.append(f"{group.category}: {', '.join(names)}")
        if skill_lines:
            sections.append(
                ResumeSection(
                    type="skills",
                    title="Skills",
                    blocks=[BulletsBlock(items=skill_lines)],
                )
            )

    if candidate.experience:
        items: list[TimelineItem] = []
        for experience in candidate.experience:
            heading = f"{experience.role} | {experience.company}"
            start = (
                experience.date_range.start
                if experience.date_range and experience.date_range.start
                else None
            )
            end = None
            if experience.date_range:
                end = "Present" if experience.date_range.is_current else experience.date_range.end
            items.append(
                TimelineItem(
                    heading=heading,
                    subheading=experience.location,
                    start=start,
                    end=end,
                    bullets=experience.bullets,
                )
            )
        sections.append(
            ResumeSection(
                type="experience",
                title="Experience",
                blocks=[TimelineBlock(items=items)],
            )
        )

    if candidate.projects:
        project_bullets: list[str] = []
        for project in candidate.projects:
            if project.description:
                project_bullets.append(f"{project.name}: {project.description}")
            else:
                project_bullets.append(project.name)
        sections.append(
            ResumeSection(
                type="projects",
                title="Projects",
                blocks=[BulletsBlock(items=project_bullets)],
            )
        )

    if candidate.education:
        education_items: list[TimelineItem] = []
        for education in candidate.education:
            degree_bits = [value for value in [education.degree, education.field_of_study] if value]
            subheading = " - ".join(degree_bits) if degree_bits else None
            start = (
                education.date_range.start
                if education.date_range and education.date_range.start
                else None
            )
            end = education.date_range.end if education.date_range and education.date_range.end else None
            education_items.append(
                TimelineItem(
                    heading=education.school,
                    subheading=subheading,
                    start=start,
                    end=end,
                    bullets=[],
                )
            )
        sections.append(
            ResumeSection(
                type="education",
                title="Education",
                blocks=[TimelineBlock(items=education_items)],
            )
        )

    if candidate.certifications:
        tags = [certification.name for certification in candidate.certifications if certification.name]
        if tags:
            sections.append(
                ResumeSection(
                    type="certifications",
                    title="Certifications",
                    blocks=[TagBlock(items=tags)],
                )
            )

    return ResumeDocument(
        resume_id=new_uuid(),
        candidate_id=candidate.candidate_id,
        template_id=template_id,
        locale=locale,
        created_at=datetime.utcnow(),
        sections=sections,
    )
