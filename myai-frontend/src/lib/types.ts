export type SkillItem = {
  name: string;
};

export type SkillGroup = {
  category: string;
  items: SkillItem[];
};

export type ExperienceItem = {
  id: string;
  company: string;
  role: string;
  location?: string | null;
  date_range?: {
    start?: string | null;
    end?: string | null;
    is_current?: boolean;
  } | null;
  summary?: string | null;
  bullets: string[];
  technologies: string[];
  achievements: string[];
};

export type ProjectItem = {
  id: string;
  name: string;
  description?: string | null;
  technologies: string[];
  bullets: string[];
};

export type CandidateProfile = {
  schema_version: "candidate_profile.v1";
  candidate_id: string;
  personal: {
    full_name: string;
    headline?: string | null;
    location?: string | null;
    pronouns?: string | null;
  };
  summary?: {
    about?: string | null;
    highlights: string[];
  } | null;
  skills: SkillGroup[];
  experience: ExperienceItem[];
  projects: ProjectItem[];
  education: unknown[];
  certifications: unknown[];
  achievements: unknown[];
  languages: unknown[];
  custom_sections: unknown[];
  links?: unknown[];
  contact?: unknown;
  meta?: unknown;
};

export type JobDescription = {
  schema_version: "job_description.v1";
  job_id: string;
  title: string;
  company?: string | null;
  location?: string | null;
  summary?: string | null;
  responsibilities: string[];
  must_have_skills: string[];
  nice_to_have_skills: string[];
  keywords: string[];
  minimum_years_experience?: number | null;
  employment_type?: "full_time" | "part_time" | "contract" | "internship" | "freelance" | null;
  work_model?: "remote" | "hybrid" | "onsite" | null;
  seniority?: "intern" | "junior" | "mid" | "senior" | "lead" | "manager" | null;
  education_preferences: string[];
};

export type MatchScoreBreakdown = {
  skill_score: number;
  keyword_score: number;
  experience_score: number;
  seniority_score: number;
};

export type CandidateMatchResult = {
  candidate_id: string;
  candidate_name: string;
  score: number;
  band: "strong" | "good" | "moderate" | "weak";
  breakdown: MatchScoreBreakdown;
  matched_skills: string[];
  missing_skills: string[];
  keyword_hits: string[];
  experience_years: number;
  highlights: string[];
  recruiter_summary?: string | null;
};

export type CandidateRankingResponse = {
  job_id: string;
  job_title: string;
  total_candidates: number;
  ranked_candidates: CandidateMatchResult[];
};

export type ResumeSection = {
  type: string;
  key?: string | null;
  title?: string | null;
  blocks: Array<Record<string, unknown>>;
};

export type ResumeTemplateDataResponse = {
  candidate?: CandidateProfile | null;
  template?: {
    template_id: string;
    display_name: string;
    template_version: string;
  } | null;
  resume: {
    resume_id: string;
    candidate_id: string;
    template_id: string;
    template_version?: string | null;
    locale: string;
    sections: ResumeSection[];
  };
  warnings: Array<{ code: string; message: string; section_key?: string | null }>;
  provenance: {
    deterministic: boolean;
    ai_used: boolean;
    ai_provider?: string | null;
    ai_model?: string | null;
    ai_enrichments: string[];
  };
};

export type ResumeChatResponse = {
  answer: string;
  provider: string;
  model: string;
};

export type AiSummaryResponse = {
  summary: string | null;
  provider?: string | null;
  model?: string | null;
};

export type RecruiterSummaryResponse = {
  summary: string;
  provider?: string | null;
  model?: string | null;
};

export type ApiErrorResponse = {
  error?: string;
  detail?: string | { msg?: string }[] | Record<string, unknown>;
  request_id?: string | null;
};
