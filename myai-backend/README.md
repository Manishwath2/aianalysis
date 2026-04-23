# myai-backend

FastAPI backend for the AI Recruitment Assistant.

## Quickstart (Local-First / PowerShell)

1. Create and activate the virtual environment

```powershell
cd "c:\SupportiveApps\Match Making Application\MyAI\myai-backend"
python -m venv .venv
.\.venv\Scripts\Activate.ps1
```

2. Install dependencies

```powershell
pip install -r requirements.txt
```

3. Configure environment

Copy `.env.example` to `.env`.

For the MVP backend, `DATABASE_URL` can stay empty.

4. Run the app

```powershell
uvicorn app.main:app --reload --port 8000
```

Open:
- Docs: http://localhost:8000/docs
- Health: http://localhost:8000/healthz
- Readiness: http://localhost:8000/readyz

## Local-First Behavior

When `DATABASE_URL` is empty, the backend still works with:
- in-memory candidate, job, and resume storage
- built-in resume templates
- Gemini, OpenWebUI, or grounded deterministic fallback responses when no external provider is configured

When `DATABASE_URL` is configured and reachable, candidate profiles, job descriptions, and generated resumes are stored in the database.

## Core Endpoints

### Candidates
- `POST /v1/candidates/validate`
- `POST /v1/candidates`
- `GET /v1/candidates/{candidate_id}`

### Jobs
- `POST /v1/jobs/validate`
- `POST /v1/jobs`
- `GET /v1/jobs`
- `GET /v1/jobs/{job_id}`

### Templates
- `GET /v1/templates`
- `GET /v1/templates/{template_id}?version=...`

### Matching
- `POST /v1/matches/score`
- `POST /v1/matches/rank`
- `POST /v1/matches/recruiter-summary`

### Resume
- `POST /v1/resumes/generate`
- `POST /v1/resumes/generate-bundle`
- `POST /v1/resumes/template-data`
- `GET /v1/resumes/{resume_id}`

### AI
- `POST /v1/ai/summary`
- `POST /v1/ai/enhance/experience`
- `POST /v1/ai/enhance/projects`
- `POST /v1/chat/resume-help`

### LLM
- `GET /v1/llm/providers`
- `GET /v1/llm/models`
- `POST /v1/chat/completions`

## Notes

- Ranking is deterministic and tuned for recruiter workflows, with must-have coverage weighted more heavily than generic keyword overlap.
- When no live LLM key is present, summary, shortlist, and recruiter-note flows fall back to grounded deterministic output rather than placeholder demo text.
