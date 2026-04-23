# AI Recruitment Assistant

End-to-end recruitment assistant with:
- `myai-backend`: FastAPI backend for candidate intake, resume JSON generation, job descriptions, ranking, recruiter summaries, and LLM-backed chat
- `myai-frontend`: Next.js mobile-first frontend for candidates, jobs, matches, template preview, and recruiter chat

## Local Development

### Backend

```powershell
cd "c:\SupportiveApps\Match Making Application\MyAI\myai-backend"
copy .env.example .env
.\.venv\Scripts\Activate.ps1
uvicorn app.main:app --reload --port 8000
```

### Frontend

```powershell
cd "c:\SupportiveApps\Match Making Application\MyAI\myai-frontend"
copy .env.example .env.local
npm install
npm run dev
```

The frontend uses a same-origin proxy route and reads `BACKEND_BASE_URL` on the server side.

## Coolify / VPS Deployment

Use the root-level `docker-compose.yml` as the stack definition.

1. Add a new Docker Compose resource in Coolify.
2. Point it at the repository root.
3. Load the variables from `.env.example` into Coolify's environment UI.
4. Assign your public domain to the `frontend` service and target container port `3000`.
5. Keep `backend` and `postgres` internal unless you explicitly need host port exposure.

Default internal service URLs in the stack:
- frontend -> backend: `http://backend:8000`
- backend -> postgres: `postgresql+asyncpg://postgres:<password>@postgres:5432/myai`

## Core Backend APIs

- `POST /v1/candidates`
- `GET /v1/candidates`
- `POST /v1/jobs`
- `GET /v1/jobs`
- `POST /v1/matches/rank`
- `POST /v1/matches/score`
- `POST /v1/matches/recruiter-summary`
- `POST /v1/resumes/template-data`
- `POST /v1/chat/resume-help`

## Notes

- Candidate ranking is deterministic for stability and low token cost.
- Recruiter summaries can use Gemini when `GEMINI_API_KEY` is set.
- If no external LLM is configured, the app still runs using deterministic fallbacks and demo chat responses.
