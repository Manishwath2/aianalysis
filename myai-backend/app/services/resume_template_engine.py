from __future__ import annotations

import re
from datetime import date, datetime

from app.schemas.candidate import CandidateProfile
from app.schemas.resume import (
    BulletsBlock,
    LinkBlock,
    ResumeDocument,
    ResumeSection,
    ResumeWarning,
    TagBlock,
    TextBlock,
    TimelineBlock,
    TimelineItem,
)
from app.schemas.templates import (
    ResumeTemplateDefinition,
    TemplateBlockBullets,
    TemplateBlockBulletsFromItems,
    TemplateBlockLinks,
    TemplateBlockSkillGroupLines,
    TemplateBlockTags,
    TemplateBlockText,
    TemplateBlockTimeline,
    TemplateLimits,
    TemplateSort,
)
from app.utils.ids import new_uuid


def _parse_date_string(value: str | None) -> date | None:
    if not value:
        return None
    try:
        if len(value) == 4:
            return date(int(value), 1, 1)
        if len(value) == 7:
            y, m = value.split("-")
            return date(int(y), int(m), 1)
        if len(value) == 10:
            y, m, d = value.split("-")
            return date(int(y), int(m), int(d))
    except Exception:
        return None
    return None


def _get_attr(obj: object, name: str) -> object | None:
    if obj is None:
        return None
    if isinstance(obj, dict):
        return obj.get(name)
    return getattr(obj, name, None)


def _resolve_path(obj: object, path: str | None) -> object | None:
    if obj is None or not path:
        return None
    cur: object | None = obj
    for segment in path.split("."):
        cur = _get_attr(cur, segment)
        if cur is None:
            return None
    return cur


_placeholder_re = re.compile(r"\{([^{}]+)\}")


def _render_template(template: str, obj: object) -> str:
    def repl(match: re.Match[str]) -> str:
        path = match.group(1).strip()
        value = _resolve_path(obj, path)
        if value is None:
            return ""
        return str(value)

    rendered = _placeholder_re.sub(repl, template)
    # Normalize whitespace a bit.
    rendered = re.sub(r"\s+", " ", rendered).strip()
    return rendered


def _missing_any(obj: object, paths: list[str]) -> bool:
    for p in paths:
        v = _resolve_path(obj, p)
        if v is None:
            return True
        if isinstance(v, str) and not v.strip():
            return True
    return False


def _apply_limits_items(items: list[object], limits: TemplateLimits | None, warnings: list[ResumeWarning], section_key: str):
    if limits and limits.max_items is not None and len(items) > limits.max_items:
        warnings.append(
            ResumeWarning(
                code="items_truncated",
                message=f"Truncated items from {len(items)} to {limits.max_items}",
                section_key=section_key,
            )
        )
        return items[: limits.max_items]
    return items


def _sort_items(items: list[object], sort: TemplateSort | None) -> list[object]:
    if not sort:
        return items
    direction = sort.direction

    present: list[tuple[tuple[int, object], object]] = []
    missing: list[object] = []

    for x in items:
        raw = _resolve_path(x, sort.by)
        if raw is None or (isinstance(raw, str) and not raw.strip()):
            missing.append(x)
            continue

        if isinstance(raw, str):
            parsed = _parse_date_string(raw)
            if parsed:
                present.append(((0, parsed.toordinal()), x))
            else:
                present.append(((2, raw), x))
            continue

        if isinstance(raw, date):
            present.append(((0, raw.toordinal()), x))
            continue

        if isinstance(raw, datetime):
            present.append(((0, int(raw.timestamp())), x))
            continue

        if isinstance(raw, (int, float)):
            present.append(((1, float(raw)), x))
            continue

        present.append(((2, str(raw)), x))

    present_sorted = sorted(present, key=lambda t: t[0], reverse=(direction == "desc"))
    return [x for _, x in present_sorted] + missing


def _non_empty_text(text: str | None) -> bool:
    return bool(text and text.strip())


def _blocks_have_content(blocks: list[object]) -> bool:
    for b in blocks:
        if isinstance(b, TextBlock) and _non_empty_text(b.text):
            return True
        if isinstance(b, BulletsBlock) and any(_non_empty_text(x) for x in b.items):
            return True
        if isinstance(b, TagBlock) and len(b.items) > 0:
            return True
        if isinstance(b, TimelineBlock) and len(b.items) > 0:
            return True
        if isinstance(b, LinkBlock) and _non_empty_text(b.label):
            return True
    return False


def _compile_custom_sections(candidate: CandidateProfile) -> list[ResumeSection]:
    sections: list[ResumeSection] = []
    for cs in candidate.custom_sections:
        blocks: list[object] = []
        for b in cs.blocks:
            if b.type == "text":
                blocks.append(TextBlock(text=b.text))
            elif b.type == "bullets":
                blocks.append(BulletsBlock(items=[x for x in b.items if _non_empty_text(x)]))
            elif b.type == "timeline":
                tl_items: list[TimelineItem] = []
                for it in b.items:
                    start = it.date_range.start if it.date_range and it.date_range.start else None
                    end = None
                    if it.date_range:
                        end = "Present" if it.date_range.is_current else it.date_range.end
                    tl_items.append(
                        TimelineItem(
                            heading=it.heading,
                            subheading=it.subheading,
                            start=start,
                            end=end,
                            bullets=[x for x in it.bullets if _non_empty_text(x)],
                        )
                    )
                blocks.append(TimelineBlock(items=tl_items))

        if _blocks_have_content(blocks):
            sections.append(ResumeSection(type="custom", key=cs.section_id, title=cs.title, blocks=blocks))
    return sections


def _compile_section_blocks(
    *,
    candidate: CandidateProfile,
    section_key: str,
    block_specs: list[object],
    warnings: list[ResumeWarning],
) -> list[object]:
    blocks: list[object] = []

    for spec in block_specs:
        if isinstance(spec, TemplateBlockText):
            if spec.source:
                value = _resolve_path(candidate, spec.source)
                if isinstance(value, str) and _non_empty_text(value):
                    blocks.append(TextBlock(text=value.strip()))
                continue

            if spec.template:
                if spec.fallback_template and _missing_any(candidate, spec.fallback_if_missing):
                    rendered = _render_template(spec.fallback_template, candidate)
                else:
                    rendered = _render_template(spec.template, candidate)
                    if spec.fallback_template and not rendered:
                        rendered = _render_template(spec.fallback_template, candidate)
                if rendered:
                    blocks.append(TextBlock(text=rendered))
                continue

        if isinstance(spec, TemplateBlockBullets):
            value = _resolve_path(candidate, spec.source)
            if isinstance(value, list):
                items = [str(x).strip() for x in value if isinstance(x, str) and _non_empty_text(x)]
                if items:
                    blocks.append(BulletsBlock(items=items))
            continue

        if isinstance(spec, TemplateBlockTags):
            value = _resolve_path(candidate, spec.source)
            if isinstance(value, list):
                tags: list[str] = []
                for item in value:
                    if spec.item_path:
                        v = _resolve_path(item, spec.item_path)
                        if isinstance(v, str) and _non_empty_text(v):
                            tags.append(v.strip())
                    else:
                        if isinstance(item, str) and _non_empty_text(item):
                            tags.append(item.strip())
                if tags:
                    blocks.append(TagBlock(items=tags))
            continue

        if isinstance(spec, TemplateBlockLinks):
            value = _resolve_path(candidate, spec.source)
            if isinstance(value, list):
                for link in value:
                    label = _resolve_path(link, "label")
                    url = _resolve_path(link, "url")
                    if isinstance(label, str) and label.strip() and url is not None:
                        blocks.append(LinkBlock(label=label.strip(), url=url))
            continue

        if isinstance(spec, TemplateBlockSkillGroupLines):
            value = _resolve_path(candidate, spec.source)
            if isinstance(value, list):
                lines: list[str] = []
                for group in value:
                    category = _resolve_path(group, "category")
                    items = _resolve_path(group, "items")
                    if not isinstance(category, str) or not category.strip() or not isinstance(items, list):
                        continue
                    names = []
                    for it in items:
                        nm = _resolve_path(it, "name")
                        if isinstance(nm, str) and _non_empty_text(nm):
                            names.append(nm.strip())
                    if names:
                        lines.append(f"{category.strip()}: {', '.join(names)}")
                if lines:
                    blocks.append(BulletsBlock(items=lines))
            continue

        if isinstance(spec, TemplateBlockBulletsFromItems):
            value = _resolve_path(candidate, spec.source)
            if isinstance(value, list):
                items = _sort_items(value, spec.sort)
                items = _apply_limits_items(items, spec.limits, warnings, section_key)
                out: list[str] = []
                for it in items:
                    if spec.fallback_template and _missing_any(it, spec.fallback_if_missing):
                        rendered = _render_template(spec.fallback_template, it)
                    else:
                        rendered = _render_template(spec.item_template, it)
                        if spec.fallback_template and (not rendered):
                            rendered = _render_template(spec.fallback_template, it)
                    if rendered:
                        out.append(rendered)
                if out:
                    blocks.append(BulletsBlock(items=out))
            continue

        if isinstance(spec, TemplateBlockTimeline):
            value = _resolve_path(candidate, spec.source)
            if isinstance(value, list):
                items = _sort_items(value, spec.sort)
                items = _apply_limits_items(items, spec.limits, warnings, section_key)
                tl_items: list[TimelineItem] = []
                for it in items:
                    heading = _render_template(spec.heading_template, it)
                    if not heading:
                        continue

                    subheading: str | None = None
                    if spec.subheading_template:
                        missing = (
                            bool(spec.subheading_fallback_template)
                            and spec.subheading_fallback_if_missing
                            and _missing_any(it, spec.subheading_fallback_if_missing)
                        )
                        if missing and spec.subheading_fallback_template:
                            subheading = _render_template(spec.subheading_fallback_template, it) or None
                        else:
                            subheading = _render_template(spec.subheading_template, it) or None
                            if not subheading and spec.subheading_fallback_template:
                                subheading = _render_template(spec.subheading_fallback_template, it) or None
                    elif spec.subheading_path:
                        v = _resolve_path(it, spec.subheading_path)
                        if isinstance(v, str) and _non_empty_text(v):
                            subheading = v.strip()

                    start: str | None = None
                    end: str | None = None
                    if spec.start_path:
                        s = _resolve_path(it, spec.start_path)
                        if isinstance(s, str) and _non_empty_text(s):
                            start = s.strip()
                    if spec.is_current_path and _resolve_path(it, spec.is_current_path) is True:
                        end = spec.end_current_value
                    elif spec.end_path:
                        e = _resolve_path(it, spec.end_path)
                        if isinstance(e, str) and _non_empty_text(e):
                            end = e.strip()

                    bullets: list[str] = []
                    if spec.bullets_path:
                        b = _resolve_path(it, spec.bullets_path)
                        if isinstance(b, list):
                            bullets = [str(x).strip() for x in b if isinstance(x, str) and _non_empty_text(x)]
                            if spec.limits and spec.limits.max_bullets_per_item is not None:
                                if len(bullets) > spec.limits.max_bullets_per_item:
                                    warnings.append(
                                        ResumeWarning(
                                            code="bullets_truncated",
                                            message=(
                                                f"Truncated bullets from {len(bullets)} to {spec.limits.max_bullets_per_item}"
                                            ),
                                            section_key=section_key,
                                        )
                                    )
                                    bullets = bullets[: spec.limits.max_bullets_per_item]

                    tl_items.append(
                        TimelineItem(
                            heading=heading,
                            subheading=subheading,
                            start=start,
                            end=end,
                            bullets=bullets,
                        )
                    )
                if tl_items:
                    blocks.append(TimelineBlock(items=tl_items))
            continue

    return blocks


def _section_type_for_key(section_key: str) -> str:
    if section_key.startswith("custom:") or section_key == "custom_sections":
        return "custom"
    return section_key


def compile_resume_bundle(
    *,
    candidate: CandidateProfile,
    template: ResumeTemplateDefinition,
    locale: str,
) -> tuple[ResumeDocument, list[ResumeWarning]]:
    warnings: list[ResumeWarning] = []
    sections: list[ResumeSection] = []

    # Pre-compile candidate custom sections once.
    custom_sections = _compile_custom_sections(candidate)
    custom_by_id = {s.key: s for s in custom_sections if s.key}

    for spec in template.sections:
        if spec.visibility.mode == "never":
            continue

        if spec.section_key == "custom_sections":
            # Insert all custom sections here.
            if spec.visibility.mode == "always" or (spec.visibility.mode == "auto" and custom_sections):
                sections.extend(custom_sections)
            continue

        if spec.section_key.startswith("custom:"):
            wanted = spec.section_key.split(":", 1)[1]
            cs = custom_by_id.get(wanted)
            if cs is None:
                continue
            if spec.visibility.mode == "auto" and not _blocks_have_content(cs.blocks):
                continue
            # Allow title override for custom sections.
            if spec.title:
                cs = ResumeSection(type=cs.type, key=cs.key, title=spec.title, blocks=cs.blocks)
            sections.append(cs)
            continue

        section_type = _section_type_for_key(spec.section_key)
        blocks = _compile_section_blocks(
            candidate=candidate,
            section_key=spec.section_key,
            block_specs=list(spec.blocks),
            warnings=warnings,
        )

        if spec.visibility.mode == "auto" and not _blocks_have_content(blocks):
            continue
        if spec.visibility.min_items is not None:
            # Approximate "items" count based on primary block types.
            count = 0
            for b in blocks:
                if isinstance(b, BulletsBlock):
                    count = max(count, len(b.items))
                elif isinstance(b, TagBlock):
                    count = max(count, len(b.items))
                elif isinstance(b, TimelineBlock):
                    count = max(count, len(b.items))
            if count < spec.visibility.min_items:
                continue

        sections.append(ResumeSection(type=section_type, title=spec.title, blocks=blocks))

    resume = ResumeDocument(
        schema_version="resume_document.v2",
        resume_id=new_uuid(),
        candidate_id=candidate.candidate_id,
        template_id=template.template_id,
        template_version=template.template_version,
        locale=locale,
        created_at=datetime.utcnow(),
        sections=sections,
    )
    return resume, warnings
