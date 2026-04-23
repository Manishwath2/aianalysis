"""create candidate, job, and resume document tables

Revision ID: 0003
Revises: 0002
Create Date: 2026-04-23
"""

from alembic import op
import sqlalchemy as sa


revision = "0003"
down_revision = "0002"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "candidate_profiles",
        sa.Column("candidate_id", sa.Uuid(), primary_key=True, nullable=False),
        sa.Column("full_name", sa.String(length=120), nullable=False),
        sa.Column("headline", sa.String(length=180), nullable=True),
        sa.Column("location", sa.String(length=120), nullable=True),
        sa.Column("source", sa.String(length=80), nullable=True),
        sa.Column("document", sa.JSON(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index(
        "ix_candidate_profiles_full_name",
        "candidate_profiles",
        ["full_name"],
        unique=False,
    )

    op.create_table(
        "job_descriptions",
        sa.Column("job_id", sa.Uuid(), primary_key=True, nullable=False),
        sa.Column("title", sa.String(length=140), nullable=False),
        sa.Column("company", sa.String(length=140), nullable=True),
        sa.Column("location", sa.String(length=120), nullable=True),
        sa.Column("seniority", sa.String(length=40), nullable=True),
        sa.Column("work_model", sa.String(length=40), nullable=True),
        sa.Column("document", sa.JSON(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_job_descriptions_title", "job_descriptions", ["title"], unique=False)

    op.create_table(
        "resume_documents",
        sa.Column("resume_id", sa.Uuid(), primary_key=True, nullable=False),
        sa.Column("candidate_id", sa.Uuid(), nullable=False),
        sa.Column("template_id", sa.String(length=60), nullable=False),
        sa.Column("template_version", sa.String(length=40), nullable=True),
        sa.Column("locale", sa.String(length=20), nullable=False),
        sa.Column("document", sa.JSON(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index(
        "ix_resume_documents_candidate_id",
        "resume_documents",
        ["candidate_id"],
        unique=False,
    )
    op.create_index(
        "ix_resume_documents_template_id",
        "resume_documents",
        ["template_id"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index("ix_resume_documents_template_id", table_name="resume_documents")
    op.drop_index("ix_resume_documents_candidate_id", table_name="resume_documents")
    op.drop_table("resume_documents")

    op.drop_index("ix_job_descriptions_title", table_name="job_descriptions")
    op.drop_table("job_descriptions")

    op.drop_index("ix_candidate_profiles_full_name", table_name="candidate_profiles")
    op.drop_table("candidate_profiles")
