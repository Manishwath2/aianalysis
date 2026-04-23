from __future__ import annotations

import os
import unittest

from fastapi.testclient import TestClient

os.environ["DATABASE_URL"] = ""

from app.core.config import get_settings

get_settings.cache_clear()

from app.main import create_app
from app.utils.memory_store import CANDIDATES, JOBS, RESUMES


def build_candidate() -> dict:
    return {
        "schema_version": "candidate_profile.v1",
        "candidate_id": "1430bbc3-0dff-45e1-a1f4-127ba5497398",
        "personal": {
            "full_name": "Ava Sharma",
            "headline": "Senior Python Backend Engineer",
            "location": "Bengaluru",
        },
        "summary": {
            "about": "Backend engineer focused on FastAPI services, recruiter workflow automation, and structured JSON APIs for AI products.",
            "highlights": [
                "Built recruiter-facing APIs",
                "Shipped matching workflows quickly",
                "Worked with LLM-powered product features",
            ],
        },
        "skills": [
            {
                "category": "Backend",
                "items": [
                    {"name": "Python"},
                    {"name": "FastAPI"},
                    {"name": "REST APIs"},
                    {"name": "Docker"},
                ],
            },
            {
                "category": "AI",
                "items": [
                    {"name": "LLMs"},
                    {"name": "Prompt Engineering"},
                ],
            },
        ],
        "experience": [
            {
                "id": "exp-ava-1",
                "company": "TalentForge",
                "role": "Senior Backend Engineer",
                "location": "Remote",
                "date_range": {"start": "2021-01", "is_current": True},
                "summary": "Built backend systems for hiring automation.",
                "bullets": [
                    "Designed APIs for recruiter workflows and candidate insights.",
                    "Improved internal screening and summary generation flows.",
                ],
                "technologies": ["Python", "FastAPI", "Docker", "PostgreSQL"],
                "achievements": ["Reduced recruiter turnaround time"],
            }
        ],
        "projects": [
            {
                "id": "proj-ava-1",
                "name": "Recruitment Copilot",
                "description": "AI-assisted matching and recruiter note generation.",
                "technologies": ["FastAPI", "LLM", "Next.js"],
                "bullets": ["Generated ranked candidate summaries for hiring teams."],
            }
        ],
        "education": [],
        "certifications": [],
        "achievements": [],
        "languages": [],
        "custom_sections": [],
    }


def build_job() -> dict:
    return {
        "schema_version": "job_description.v1",
        "job_id": "e070406f-6a11-442e-b847-884012ebc90c",
        "title": "AI Recruitment Backend Engineer",
        "company": "TalentFlow",
        "location": "Remote",
        "summary": "Build matching, ranking, and recruiter summary services for AI hiring products.",
        "responsibilities": [
            "Design FastAPI services for candidate analysis",
            "Build structured JSON contracts for frontend rendering",
            "Support recruiter ranking and summary workflows",
        ],
        "must_have_skills": ["Python", "FastAPI", "REST APIs"],
        "nice_to_have_skills": ["Docker", "LLMs", "Prompt Engineering"],
        "keywords": ["matching", "ranking", "recruiter", "summary"],
        "minimum_years_experience": 3,
        "employment_type": "full_time",
        "work_model": "remote",
        "seniority": "senior",
        "education_preferences": [],
    }


class RecruitmentWorkflowTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.client = TestClient(create_app())

    def setUp(self) -> None:
        CANDIDATES.clear()
        JOBS.clear()
        RESUMES.clear()
        self.client.post("/v1/candidates", json=build_candidate())
        self.client.post("/v1/jobs", json=build_job())

    def test_ai_summary_returns_grounded_fallback(self) -> None:
        response = self.client.post("/v1/ai/summary", json={"candidate": build_candidate()})
        self.assertEqual(response.status_code, 200)
        payload = response.json()
        self.assertEqual(payload["provider"], "demo")
        self.assertIn("Senior Python Backend Engineer", payload["summary"])
        self.assertNotIn("Demo response", payload["summary"])

    def test_ranking_preserves_human_skill_labels(self) -> None:
        response = self.client.post(
            "/v1/matches/rank",
            json={
                "job_id": build_job()["job_id"],
                "include_recruiter_summary": True,
                "summary_options": {"enabled": True},
            },
        )
        self.assertEqual(response.status_code, 200)
        payload = response.json()
        top = payload["ranked_candidates"][0]
        self.assertIn("REST APIs", top["matched_skills"])
        self.assertIn("Prompt Engineering", top["matched_skills"])
        self.assertIn("Ava Sharma", top["recruiter_summary"])
        self.assertNotIn("Demo response", top["recruiter_summary"])

    def test_resume_help_shortlist_answer_is_context_aware(self) -> None:
        response = self.client.post(
            "/v1/chat/resume-help",
            json={
                "candidate_id": build_candidate()["candidate_id"],
                "job_id": build_job()["job_id"],
                "message": "Should I shortlist this candidate for the job?",
            },
        )
        self.assertEqual(response.status_code, 200)
        payload = response.json()
        self.assertEqual(payload["provider"], "demo")
        self.assertIn("shortlist", payload["answer"].lower())
        self.assertIn("score", payload["answer"].lower())

    def test_template_data_resolves_candidate_by_id(self) -> None:
        response = self.client.post(
            "/v1/resumes/template-data",
            json={
                "candidate_id": build_candidate()["candidate_id"],
                "template_id": "classic",
                "include_candidate": True,
                "include_template": True,
            },
        )
        self.assertEqual(response.status_code, 200)
        payload = response.json()
        self.assertEqual(payload["candidate"]["candidate_id"], build_candidate()["candidate_id"])
        self.assertEqual(payload["resume"]["template_id"], "classic")


if __name__ == "__main__":
    unittest.main()
