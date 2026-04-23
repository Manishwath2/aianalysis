import type { CandidateProfile, JobDescription } from "@/lib/types";

function createId() {
  if (typeof crypto !== "undefined" && "randomUUID" in crypto) {
    return crypto.randomUUID();
  }
  return `${Date.now()}-${Math.random().toString(16).slice(2)}`;
}

export function buildSampleCandidate(): CandidateProfile {
  return {
    schema_version: "candidate_profile.v1",
    candidate_id: createId(),
    personal: {
      full_name: "Ava Sharma",
      headline: "Senior Python Backend Engineer",
      location: "Bengaluru",
    },
    summary: {
      about:
        "Backend engineer focused on FastAPI services, recruiter workflow automation, and structured JSON APIs for AI products.",
      highlights: [
        "Built recruiter-facing APIs",
        "Shipped matching workflows quickly",
        "Worked with LLM-powered product features",
      ],
    },
    skills: [
      {
        category: "Backend",
        items: [
          { name: "Python" },
          { name: "FastAPI" },
          { name: "REST APIs" },
          { name: "Docker" },
        ],
      },
      {
        category: "AI",
        items: [{ name: "LLMs" }, { name: "Prompt Engineering" }],
      },
    ],
    experience: [
      {
        id: createId(),
        company: "TalentForge",
        role: "Senior Backend Engineer",
        location: "Remote",
        date_range: {
          start: "2021-01",
          is_current: true,
        },
        summary: "Built backend systems for hiring automation.",
        bullets: [
          "Designed APIs for recruiter workflows and candidate insights.",
          "Improved internal screening and summary generation flows.",
        ],
        technologies: ["Python", "FastAPI", "Docker", "PostgreSQL"],
        achievements: ["Reduced recruiter turnaround time"],
      },
    ],
    projects: [
      {
        id: createId(),
        name: "Recruitment Copilot",
        description: "AI-assisted matching and recruiter note generation.",
        technologies: ["FastAPI", "LLM", "Next.js"],
        bullets: ["Generated ranked candidate summaries for hiring teams."],
      },
    ],
    education: [],
    certifications: [],
    achievements: [],
    languages: [],
    custom_sections: [],
  };
}

export function buildSampleJob(): JobDescription {
  return {
    schema_version: "job_description.v1",
    job_id: createId(),
    title: "AI Recruitment Backend Engineer",
    company: "TalentFlow",
    location: "Remote",
    summary: "Build matching, ranking, and recruiter summary services for AI hiring products.",
    responsibilities: [
      "Design FastAPI services for candidate analysis",
      "Build structured JSON contracts for frontend rendering",
      "Support recruiter ranking and summary workflows",
    ],
    must_have_skills: ["Python", "FastAPI", "REST APIs"],
    nice_to_have_skills: ["Docker", "LLMs", "Prompt Engineering"],
    keywords: ["matching", "ranking", "recruiter", "summary"],
    minimum_years_experience: 3,
    employment_type: "full_time",
    work_model: "remote",
    seniority: "senior",
    education_preferences: [],
  };
}
