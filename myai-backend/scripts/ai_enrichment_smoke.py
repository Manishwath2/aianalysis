from __future__ import annotations

import json
import uuid

import httpx

BASE = "http://127.0.0.1:8000"

candidate_id = str(uuid.uuid4())

candidate = {
    "candidate_id": candidate_id,
    "personal": {
        "full_name": "Test User",
        "headline": "Backend Engineer",
        "location": "Remote",
    },
    "summary": {"about": "", "highlights": []},
    "skills": [
        {
            "category": "Languages",
            "items": [
                {"name": "Python", "level": "advanced"},
                {"name": "TypeScript", "level": "intermediate"},
            ],
        }
    ],
    "experience": [
        {
            "id": "exp-1",
            "company": "Acme Corp",
            "role": "Software Engineer",
            "location": "Remote",
            "date_range": {"start": "2021-01", "end": "2023-12", "is_current": False},
            "summary": "Built backend services for hiring workflows.",
            "bullets": [],
            "technologies": ["FastAPI", "PostgreSQL"],
            "achievements": ["Reduced API latency by 35%"],
        }
    ],
    "projects": [
        {
            "id": "proj-1",
            "name": "Resume Builder",
            "description": "Template-driven resume generation service.",
            "date_range": {"start": "2023-01", "end": "2023-06", "is_current": False},
            "links": [],
            "technologies": ["FastAPI", "SQLAlchemy"],
            "bullets": [],
        }
    ],
}

payload = {
    "template_id": "classic",
    "locale": "en-US",
    "candidate": candidate,
    "include_candidate": True,
    "include_template": True,
    "ai": {
        "enabled": True,
        "enrichments": ["summary", "experience_bullets", "project_bullets"],
        "provider": "demo",
        "model": "demo/default",
    },
}

with httpx.Client(timeout=30) as client:
    resp = client.post(f"{BASE}/v1/resumes/generate-bundle", json=payload)

print("status", resp.status_code)
try:
    data = resp.json()
    print(json.dumps(data, ensure_ascii=False, indent=2))
except Exception:
    print(resp.text)
