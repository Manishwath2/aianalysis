import type {
  AiSummaryResponse,
  CandidateProfile,
  CandidateRankingResponse,
  JobDescription,
  RecruiterSummaryResponse,
  ResumeChatResponse,
  ResumeTemplateDataResponse,
} from "@/lib/types";

const API_PREFIX = "/api/backend/v1";

function normalizeErrorDetail(payload: unknown, fallback: string) {
  if (!payload || typeof payload !== "object") {
    return fallback;
  }

  const data = payload as { detail?: unknown; error?: unknown; message?: unknown };
  const value = data.detail ?? data.error ?? data.message;

  if (typeof value === "string") {
    return value;
  }

  if (Array.isArray(value)) {
    return value
      .map((item) => {
        if (item && typeof item === "object" && "msg" in item) {
          return String((item as { msg: unknown }).msg);
        }
        return String(item);
      })
      .filter(Boolean)
      .join("; ");
  }

  if (value && typeof value === "object") {
    return JSON.stringify(value);
  }

  return fallback;
}

async function apiRequest<T>(path: string, init?: RequestInit): Promise<T> {
  const response = await fetch(`${API_PREFIX}${path}`, {
    ...init,
    headers: {
      "content-type": "application/json",
      ...(init?.headers ?? {}),
    },
    cache: "no-store",
  });

  if (!response.ok) {
    let detail = `Request failed (${response.status})`;
    const rawBody = await response.text();

    try {
      const payload = rawBody ? JSON.parse(rawBody) : null;
      detail = normalizeErrorDetail(payload, detail);
    } catch {
      detail = rawBody || detail;
    }

    throw new Error(detail || "Request failed");
  }

  return (await response.json()) as T;
}

export function listCandidates() {
  return apiRequest<CandidateProfile[]>("/candidates");
}

export function createCandidate(candidate: CandidateProfile) {
  return apiRequest<CandidateProfile>("/candidates", {
    method: "POST",
    body: JSON.stringify(candidate),
  });
}

export function listJobs() {
  return apiRequest<JobDescription[]>("/jobs");
}

export function createJob(job: JobDescription) {
  return apiRequest<JobDescription>("/jobs", {
    method: "POST",
    body: JSON.stringify(job),
  });
}

export function generateResumeSummary(candidate: CandidateProfile) {
  return apiRequest<AiSummaryResponse>("/ai/summary", {
    method: "POST",
    body: JSON.stringify({
      candidate,
    }),
  });
}

export function rankCandidates(jobId: string) {
  return apiRequest<CandidateRankingResponse>("/matches/rank", {
    method: "POST",
    body: JSON.stringify({
      job_id: jobId,
      include_recruiter_summary: true,
      summary_options: {
        enabled: true,
      },
    }),
  });
}

export function generateTemplateData(candidateId: string, templateId = "classic") {
  return apiRequest<ResumeTemplateDataResponse>("/resumes/template-data", {
    method: "POST",
    body: JSON.stringify({
      candidate_id: candidateId,
      template_id: templateId,
      include_candidate: true,
      include_template: true,
    }),
  });
}

export function generateRecruiterSummary(input: { candidateId: string; jobId: string }) {
  return apiRequest<RecruiterSummaryResponse>("/matches/recruiter-summary", {
    method: "POST",
    body: JSON.stringify({
      candidate_id: input.candidateId,
      job_id: input.jobId,
      options: {
        enabled: true,
      },
    }),
  });
}

export function sendRecruitmentChat(input: {
  message: string;
  candidateId?: string;
  jobId?: string;
}) {
  return apiRequest<ResumeChatResponse>("/chat/resume-help", {
    method: "POST",
    body: JSON.stringify({
      message: input.message,
      candidate_id: input.candidateId ?? null,
      job_id: input.jobId ?? null,
    }),
  });
}
