from __future__ import annotations

from typing import Dict, List, Set

from app.schemas.candidate import CandidateProfile
from app.schemas.chat import ChatMessageCreateRequest
from app.schemas.job import JobDescription
from app.schemas.resume import ResumeDocument

# Chunk 2 will replace this with PostgreSQL persistence.

CANDIDATES: Dict[str, CandidateProfile] = {}
JOBS: Dict[str, JobDescription] = {}
RESUMES: Dict[str, ResumeDocument] = {}

CHAT_SESSIONS: Set[str] = set()
CHAT_MESSAGES: Dict[str, List[ChatMessageCreateRequest]] = {}
