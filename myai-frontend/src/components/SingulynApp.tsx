"use client";

import { useEffect, useRef, useState, type ChangeEvent, type KeyboardEvent, type ReactNode } from "react";
import {
  Bell,
  Bookmark,
  Briefcase,
  BrainCircuit,
  CheckCircle2,
  ChevronDown,
  Clock3,
  FileJson,
  FileText,
  Folder,
  Home,
  Lightbulb,
  LogOut,
  Menu,
  MessageSquare,
  Plus,
  RefreshCcw,
  Send,
  Settings,
  Sliders,
  Sparkles,
  Target,
  Trophy,
  User,
  Users,
  type LucideIcon,
} from "lucide-react";

import {
  createCandidate,
  createJob,
  generateRecruiterSummary,
  generateResumeSummary,
  generateTemplateData,
  listCandidates,
  listJobs,
  rankCandidates,
  sendRecruitmentChat,
} from "@/lib/api";
import { buildSampleCandidate, buildSampleJob } from "@/lib/sample-data";
import type {
  CandidateMatchResult,
  CandidateProfile,
  CandidateRankingResponse,
  JobDescription,
  ResumeTemplateDataResponse,
} from "@/lib/types";

type DrawerView = "menu" | "notifications" | "settings";
type Screen = "dashboard" | "candidates" | "jobs" | "matches" | "chat";
type Tool =
  | "Recruitment Assistant"
  | "Resume Summary"
  | "Candidate Ranking"
  | "Recruiter Notes"
  | "Template JSON";
type AssistantStatus = "idle" | "thinking" | "processing" | "generating";
type ChatRole = "user" | "assistant";

type ChatMessage = {
  id: string;
  role: ChatRole;
  text: string;
  timestamp: number;
  files?: string[];
};

type NotificationItem = {
  id: string;
  title: string;
  body: string;
  timestamp: number;
  unread: boolean;
};

type ToolResult = {
  text: string;
  nextScreen?: Screen;
};

type CandidateDraft = {
  fullName: string;
  headline: string;
  location: string;
  summary: string;
  skills: string;
  role: string;
  company: string;
  experienceYears: string;
};

type JobDraft = {
  title: string;
  company: string;
  location: string;
  summary: string;
  mustHaveSkills: string;
  niceToHaveSkills: string;
  keywords: string;
  minimumYears: string;
  seniority: JobDescription["seniority"];
};

const emptyCandidateDraft: CandidateDraft = {
  fullName: "",
  headline: "",
  location: "",
  summary: "",
  skills: "",
  role: "",
  company: "",
  experienceYears: "3",
};

const emptyJobDraft: JobDraft = {
  title: "",
  company: "",
  location: "",
  summary: "",
  mustHaveSkills: "",
  niceToHaveSkills: "",
  keywords: "",
  minimumYears: "3",
  seniority: "mid",
};

function createId(prefix: string) {
  if (typeof crypto !== "undefined" && "randomUUID" in crypto) {
    return `${prefix}-${crypto.randomUUID()}`;
  }
  return `${prefix}-${Date.now()}-${Math.random().toString(16).slice(2)}`;
}

function createUuid() {
  if (typeof crypto !== "undefined" && "randomUUID" in crypto) {
    return crypto.randomUUID();
  }
  return "10000000-1000-4000-8000-100000000000".replace(/[018]/g, (character) =>
    (
      Number(character) ^
      (Math.random() * 16) >> (Number(character) / 4)
    ).toString(16),
  );
}

function parseCsv(input: string) {
  return input
    .split(",")
    .map((item) => item.trim())
    .filter(Boolean);
}

function buildCandidatePayload(draft: CandidateDraft): CandidateProfile {
  const currentYear = new Date().getFullYear();
  const years = Number.parseFloat(draft.experienceYears || "0");
  const startYear = Number.isFinite(years) ? Math.max(currentYear - Math.round(years), 2000) : currentYear - 3;
  const skills = parseCsv(draft.skills);

  return {
    schema_version: "candidate_profile.v1",
    candidate_id: createUuid(),
    personal: {
      full_name: draft.fullName,
      headline: draft.headline || null,
      location: draft.location || null,
      pronouns: null,
    },
    summary: {
      about: draft.summary || null,
      highlights: skills.slice(0, 3).map((skill) => `${skill} delivery`),
    },
    skills: [
      {
        category: "Core Skills",
        items: skills.map((skill) => ({ name: skill })),
      },
    ],
    experience: [
      {
        id: createId("exp"),
        company: draft.company || "Current Company",
        role: draft.role || draft.headline || "Software Engineer",
        location: draft.location || null,
        date_range: {
          start: `${startYear}-01`,
          end: null,
          is_current: true,
        },
        summary: draft.summary || null,
        bullets: [
          `Delivered production work across ${skills.slice(0, 3).join(", ") || "backend systems"}.`,
        ],
        technologies: skills,
        achievements: [],
      },
    ],
    projects: [],
    education: [],
    certifications: [],
    achievements: [],
    languages: [],
    custom_sections: [],
    links: [],
    contact: null,
    meta: null,
  };
}

function buildJobPayload(draft: JobDraft): JobDescription {
  return {
    schema_version: "job_description.v1",
    job_id: createUuid(),
    title: draft.title,
    company: draft.company || null,
    location: draft.location || null,
    summary: draft.summary || null,
    responsibilities: draft.summary
      ? [draft.summary]
      : ["Deliver recruiter-facing matching and ranking workflows."],
    must_have_skills: parseCsv(draft.mustHaveSkills),
    nice_to_have_skills: parseCsv(draft.niceToHaveSkills),
    keywords: parseCsv(draft.keywords),
    minimum_years_experience: Number.parseFloat(draft.minimumYears || "0") || null,
    employment_type: "full_time",
    work_model: "remote",
    seniority: draft.seniority ?? null,
    education_preferences: [],
  };
}

function getToolPlaceholder(tool: Tool) {
  switch (tool) {
    case "Resume Summary":
      return "Generate a polished summary or ask for a tone change";
    case "Candidate Ranking":
      return "Run ranking or ask why a candidate fits the role";
    case "Recruiter Notes":
      return "Generate recruiter notes or shortlist feedback";
    case "Template JSON":
      return "Generate template JSON or ask about render sections";
    default:
      return "Ask about resume help, hiring fit, or candidate guidance";
  }
}

function getStatusLabel(status: AssistantStatus, tool: Tool) {
  if (status === "processing") {
    return tool === "Template JSON" ? "Structuring" : "Processing";
  }
  if (status === "generating") {
    return tool === "Template JSON" ? "Generating JSON" : "Generating";
  }
  return "Thinking";
}

function getPendingStatus(tool: Tool, hasInstruction: boolean): AssistantStatus {
  if (tool === "Candidate Ranking") {
    return "processing";
  }
  if (tool === "Template JSON") {
    return hasInstruction ? "processing" : "generating";
  }
  if (tool === "Resume Summary" || tool === "Recruiter Notes") {
    return hasInstruction ? "thinking" : "generating";
  }
  return "thinking";
}

function getToolExecutionHint(tool: Tool) {
  switch (tool) {
    case "Resume Summary":
      return "Tap send to generate a polished summary instantly.";
    case "Candidate Ranking":
      return "Tap send to rank all saved candidates for the selected job.";
    case "Recruiter Notes":
      return "Tap send to draft recruiter-ready notes for the current match.";
    case "Template JSON":
      return "Tap send to generate frontend-ready template JSON.";
    default:
      return null;
  }
}

function getToolRequirementNote(tool: Tool, hasCandidate: boolean, hasJob: boolean) {
  switch (tool) {
    case "Resume Summary":
    case "Template JSON":
      return hasCandidate ? null : "Select a candidate to run this tool.";
    case "Candidate Ranking":
      return hasJob ? null : "Select a job to run ranking.";
    case "Recruiter Notes":
      if (!hasCandidate && !hasJob) {
        return "Select both a candidate and a job to draft recruiter notes.";
      }
      if (!hasCandidate) {
        return "Select a candidate to draft recruiter notes.";
      }
      if (!hasJob) {
        return "Select a job to draft recruiter notes.";
      }
      return null;
    default:
      return null;
  }
}

function formatRankingMessage(result: CandidateRankingResponse) {
  const top = result.ranked_candidates.slice(0, 3);
  if (!top.length) {
    return `No candidates were available to rank for ${result.job_title}.`;
  }
  return [
    `Ranking complete for ${result.job_title}.`,
    ...top.map(
      (item, index) =>
        `${index + 1}. ${item.candidate_name} - ${item.score}% (${item.band} fit)${
          item.recruiter_summary ? `\n${item.recruiter_summary}` : ""
        }`,
    ),
    "Open Matches for the full breakdown and scorecards.",
  ].join("\n\n");
}

function formatTemplateMessage(preview: ResumeTemplateDataResponse) {
  const names = preview.resume.sections
    .slice(0, 6)
    .map((section) => section.title ?? section.type)
    .join(", ");
  return `Template JSON generated successfully. Template: ${preview.resume.template_id}. Sections: ${preview.resume.sections.length}. Preview blocks: ${names}. Open Home to inspect the latest payload cards.`;
}

export default function SingulynApp() {
  const [screen, setScreen] = useState<Screen>("chat");
  const [activeTool, setActiveTool] = useState<Tool>("Recruitment Assistant");
  const [drawerView, setDrawerView] = useState<DrawerView>("menu");
  const [isDrawerOpen, setIsDrawerOpen] = useState(false);
  const [enterToSend, setEnterToSend] = useState(true);
  const [assistantStatus, setAssistantStatus] = useState<AssistantStatus>("idle");
  const [draft, setDraft] = useState("");
  const [attachments, setAttachments] = useState<File[]>([]);
  const [candidateDraft, setCandidateDraft] = useState<CandidateDraft>(emptyCandidateDraft);
  const [jobDraft, setJobDraft] = useState<JobDraft>(emptyJobDraft);
  const [candidates, setCandidates] = useState<CandidateProfile[]>([]);
  const [jobs, setJobs] = useState<JobDescription[]>([]);
  const [ranking, setRanking] = useState<CandidateRankingResponse | null>(null);
  const [resumePreview, setResumePreview] = useState<ResumeTemplateDataResponse | null>(null);
  const [selectedCandidateId, setSelectedCandidateId] = useState<string>("");
  const [selectedJobId, setSelectedJobId] = useState<string>("");
  const [busyNote, setBusyNote] = useState<string | null>(null);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);
  const [notifications, setNotifications] = useState<NotificationItem[]>([
    {
      id: createId("notification"),
      title: "Backend Ready",
      body: "Connect candidates, jobs, ranking, and chat from one mobile workspace.",
      timestamp: Date.now(),
      unread: true,
    },
  ]);
  const [messages, setMessages] = useState<ChatMessage[]>([
    {
      id: createId("msg"),
      role: "assistant",
      text:
        "Chat is ready. Select a candidate and job, then use the tool menu for summaries, ranking, recruiter notes, or template JSON.",
      timestamp: Date.now(),
    },
  ]);

  const fileInputRef = useRef<HTMLInputElement | null>(null);
  const messagesEndRef = useRef<HTMLDivElement | null>(null);

  const hasUnreadNotifications = notifications.some((item) => item.unread);
  const selectedCandidate = candidates.find((item) => item.candidate_id === selectedCandidateId) ?? null;
  const selectedJob = jobs.find((item) => item.job_id === selectedJobId) ?? null;
  const isChatScreen = screen === "chat";
  const hasDraftInput = draft.trim().length > 0 || attachments.length > 0;
  const toolRequirementNote = getToolRequirementNote(
    activeTool,
    Boolean(selectedCandidate),
    Boolean(selectedJob),
  );
  const canRunActiveToolWithoutInput =
    activeTool !== "Recruitment Assistant" && toolRequirementNote === null;
  const canSend =
    activeTool === "Recruitment Assistant"
      ? hasDraftInput
      : toolRequirementNote === null && (hasDraftInput || canRunActiveToolWithoutInput);
  const toolExecutionHint =
    !hasDraftInput && toolRequirementNote === null ? getToolExecutionHint(activeTool) : null;

  useEffect(() => {
    void refreshData();
  }, []);

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ block: "end" });
  }, [messages, assistantStatus]);

  useEffect(() => {
    if (!isDrawerOpen) {
      return;
    }

    const previousOverflow = document.body.style.overflow;
    document.body.style.overflow = "hidden";
    return () => {
      document.body.style.overflow = previousOverflow;
    };
  }, [isDrawerOpen]);

  async function refreshData() {
    try {
      setBusyNote("Syncing recruitment workspace");
      const [candidateList, jobList] = await Promise.all([listCandidates(), listJobs()]);
      setCandidates(candidateList);
      setJobs(jobList);

      if (!selectedCandidateId && candidateList[0]) {
        setSelectedCandidateId(candidateList[0].candidate_id);
      }
      if (!selectedJobId && jobList[0]) {
        setSelectedJobId(jobList[0].job_id);
      }
      setErrorMessage(null);
    } catch (error) {
      setErrorMessage(error instanceof Error ? error.message : "Failed to load data");
    } finally {
      setBusyNote(null);
    }
  }

  function closeDrawer() {
    setIsDrawerOpen(false);
    setDrawerView("menu");
  }

  function openDrawer(view: DrawerView) {
    setDrawerView(view);
    setIsDrawerOpen(true);
    if (view === "notifications") {
      setNotifications((current) => current.map((item) => ({ ...item, unread: false })));
    }
  }

  function pushNotification(title: string, body: string) {
    setNotifications((current) => [
      {
        id: createId("notification"),
        title,
        body,
        timestamp: Date.now(),
        unread: true,
      },
      ...current,
    ]);
  }

  function resetChat() {
    setMessages([
      {
        id: createId("msg"),
        role: "assistant",
        text:
          "Fresh chat started. I can work with the selected candidate and job context immediately.",
        timestamp: Date.now(),
      },
    ]);
    setDraft("");
    setAttachments([]);
  }

  function pushAssistantMessage(text: string) {
    setMessages((current) => [
      ...current,
      {
        id: createId("msg"),
        role: "assistant",
        text,
        timestamp: Date.now(),
      },
    ]);
  }

  async function runChatTool(inputText: string, files: string[]): Promise<ToolResult> {
    const backendMessage = files.length
      ? `${inputText}\n\nAttached file names: ${files.join(", ")}`
      : inputText;

    switch (activeTool) {
      case "Resume Summary": {
        if (!selectedCandidate) {
          throw new Error("Select a candidate before generating a summary");
        }

        if (inputText) {
          const response = await sendRecruitmentChat({
            message: `Create a resume summary for the selected candidate. Additional instruction: ${backendMessage}`,
            candidateId: selectedCandidateId || undefined,
            jobId: selectedJobId || undefined,
          });
          return { text: response.answer };
        }

        const response = await generateResumeSummary(selectedCandidate);
        return {
          text:
            response.summary ??
            "Summary generation returned an empty result. Try again with more candidate details.",
        };
      }

      case "Candidate Ranking": {
        if (!selectedJobId) {
          throw new Error("Select a job before running ranking");
        }

        if (inputText) {
          const response = await sendRecruitmentChat({
            message: `Explain the likely ranking fit for the selected candidate and job. User instruction: ${backendMessage}`,
            candidateId: selectedCandidateId || undefined,
            jobId: selectedJobId || undefined,
          });
          return { text: response.answer };
        }

        const result = await rankCandidates(selectedJobId);
        setRanking(result);
        return {
          text: formatRankingMessage(result),
        };
      }

      case "Recruiter Notes": {
        if (!selectedCandidateId || !selectedJobId) {
          throw new Error("Select both a candidate and a job before generating recruiter notes");
        }

        if (inputText) {
          const response = await sendRecruitmentChat({
            message: `Write recruiter notes for the selected candidate and job. Additional instruction: ${backendMessage}`,
            candidateId: selectedCandidateId,
            jobId: selectedJobId,
          });
          return { text: response.answer };
        }

        const response = await generateRecruiterSummary({
          candidateId: selectedCandidateId,
          jobId: selectedJobId,
        });
        return { text: response.summary };
      }

      case "Template JSON": {
        if (!selectedCandidateId) {
          throw new Error("Select a candidate before generating template JSON");
        }

        const preview = await generateTemplateData(selectedCandidateId);
        setResumePreview(preview);

        if (inputText) {
          const response = await sendRecruitmentChat({
            message: `Explain the generated resume template JSON for the selected candidate. Additional instruction: ${backendMessage}`,
            candidateId: selectedCandidateId,
            jobId: selectedJobId || undefined,
          });
          return { text: `${formatTemplateMessage(preview)}\n\n${response.answer}` };
        }

        return {
          text: formatTemplateMessage(preview),
        };
      }

      default: {
        const response = await sendRecruitmentChat({
          message: backendMessage || "Help me with the selected candidate and job.",
          candidateId: selectedCandidateId || undefined,
          jobId: selectedJobId || undefined,
        });
        return { text: response.answer };
      }
    }
  }

  async function handleSeedWorkspace() {
    try {
      setBusyNote("Creating sample candidate and job");
      const [candidate, job] = await Promise.all([
        createCandidate(buildSampleCandidate()),
        createJob(buildSampleJob()),
      ]);
      await refreshData();
      setSelectedCandidateId(candidate.candidate_id);
      setSelectedJobId(job.job_id);
      pushNotification("Sample data added", "Created demo candidate and job for ranking.");
      setScreen("dashboard");
      setErrorMessage(null);
    } catch (error) {
      setErrorMessage(error instanceof Error ? error.message : "Failed to create sample data");
    } finally {
      setBusyNote(null);
    }
  }

  async function handleCreateCandidate() {
    try {
      setBusyNote("Saving candidate");
      const candidate = await createCandidate(buildCandidatePayload(candidateDraft));
      await refreshData();
      setSelectedCandidateId(candidate.candidate_id);
      setCandidateDraft(emptyCandidateDraft);
      pushNotification("Candidate saved", `${candidate.personal.full_name} is ready for matching.`);
      setScreen("candidates");
      setErrorMessage(null);
    } catch (error) {
      setErrorMessage(error instanceof Error ? error.message : "Failed to save candidate");
    } finally {
      setBusyNote(null);
    }
  }

  async function handleCreateJob() {
    try {
      setBusyNote("Saving job");
      const job = await createJob(buildJobPayload(jobDraft));
      await refreshData();
      setSelectedJobId(job.job_id);
      setJobDraft(emptyJobDraft);
      pushNotification("Job saved", `${job.title} is ready for ranking.`);
      setScreen("jobs");
      setErrorMessage(null);
    } catch (error) {
      setErrorMessage(error instanceof Error ? error.message : "Failed to save job");
    } finally {
      setBusyNote(null);
    }
  }

  async function handleRankCandidates() {
    if (!selectedJobId) {
      setErrorMessage("Select a job before running ranking");
      return;
    }

    try {
      setBusyNote("Ranking candidates");
      const result = await rankCandidates(selectedJobId);
      setRanking(result);
      setScreen("matches");
      pushNotification("Ranking complete", `Scored ${result.total_candidates} candidate profiles.`);
      setErrorMessage(null);
    } catch (error) {
      setErrorMessage(error instanceof Error ? error.message : "Failed to rank candidates");
    } finally {
      setBusyNote(null);
    }
  }

  async function handleGenerateTemplate() {
    if (!selectedCandidateId) {
      setErrorMessage("Select a candidate before generating template JSON");
      return;
    }

    try {
      setBusyNote("Generating template JSON");
      const preview = await generateTemplateData(selectedCandidateId);
      setResumePreview(preview);
      pushNotification(
        "Template JSON ready",
        `${preview.resume.sections.length} sections prepared for frontend rendering.`,
      );
      setErrorMessage(null);
    } catch (error) {
      setErrorMessage(error instanceof Error ? error.message : "Failed to generate template data");
    } finally {
      setBusyNote(null);
    }
  }

  async function handleSend() {
    const text = draft.trim();
    if (!canSend) {
      return;
    }

    const files = attachments.map((file) => file.name);
    const userText =
      text || (files.length ? "Shared context attachments" : `Run ${activeTool}`);

    setMessages((current) => [
      ...current,
      {
        id: createId("msg"),
        role: "user",
        text: userText,
        timestamp: Date.now(),
        files: files.length ? files : undefined,
      },
    ]);
    setDraft("");
    setAttachments([]);
    setAssistantStatus(getPendingStatus(activeTool, Boolean(text || files.length)));

    try {
      const result = await runChatTool(text, files);
      setAssistantStatus("idle");
      pushAssistantMessage(result.text);
      if (result.nextScreen) {
        setScreen(result.nextScreen);
      }
      setErrorMessage(null);
    } catch (error) {
      const detail = error instanceof Error ? error.message : "Chat request failed";
      setAssistantStatus("idle");
      pushAssistantMessage(`Request failed: ${detail}`);
      setErrorMessage(detail);
    } finally {
      setAssistantStatus("idle");
    }
  }

  function handleKeyDown(event: KeyboardEvent<HTMLInputElement>) {
    if (!enterToSend || event.key !== "Enter") {
      return;
    }
    event.preventDefault();
    void handleSend();
  }

  function handleAddAttachmentClick() {
    fileInputRef.current?.click();
  }

  function handleFileChange(event: ChangeEvent<HTMLInputElement>) {
    const files = Array.from(event.target.files ?? []);
    if (!files.length) {
      return;
    }
    setAttachments((current) => [...current, ...files].slice(0, 5));
    event.target.value = "";
  }

  function removeAttachment(index: number) {
    setAttachments((current) => current.filter((_, itemIndex) => itemIndex !== index));
  }

  return (
    <div className="relative h-dvh overflow-hidden bg-[#020206] selection:bg-cyan-400/30">
      <div className="relative mx-auto flex h-dvh w-full max-w-[430px] flex-col overflow-hidden bg-[#020206] text-white">
        <div className="pointer-events-none absolute inset-0">
          <div className="absolute -top-20 left-1/2 h-64 w-64 -translate-x-1/2 rounded-full bg-cyan-400/10 blur-3xl" />
          <div className="absolute top-1/3 right-0 h-64 w-64 rounded-full bg-fuchsia-500/10 blur-3xl" />
          <div className="absolute bottom-0 left-0 h-52 w-52 rounded-full bg-blue-500/10 blur-3xl" />
        </div>

        <div className="relative z-20 flex items-center justify-between px-5 pb-2 pt-[calc(env(safe-area-inset-top)+12px)]">
          <button
            onClick={() => openDrawer("menu")}
            className="rounded-full p-2 text-gray-300 transition-colors hover:text-white"
            aria-label="Open menu"
            type="button"
          >
            <Menu className="h-[22px] w-[22px]" />
          </button>

          <button
            className="flex min-w-0 max-w-[220px] items-center space-x-2 rounded-full border border-white/10 bg-white/5 px-4 py-2 shadow-lg shadow-cyan-500/10 backdrop-blur-md transition hover:bg-white/10"
            type="button"
            aria-label="Open tool menu"
            onClick={() => openDrawer("menu")}
          >
            <Sparkles className="h-4 w-4 text-cyan-400" />
            <span className="truncate text-[13px] font-medium">{activeTool}</span>
            <ChevronDown className="h-4 w-4 text-gray-400" />
          </button>

          <div className="flex items-center space-x-3">
            <button
              className="relative rounded-full p-2 text-gray-300 transition-colors hover:text-white"
              aria-label="Notifications"
              type="button"
              onClick={() => openDrawer("notifications")}
            >
              <Bell className="h-[22px] w-[22px]" />
              {hasUnreadNotifications ? (
                <span className="absolute right-1.5 top-1.5 h-2.5 w-2.5 rounded-full border-2 border-[#020206] bg-fuchsia-500" />
              ) : null}
            </button>
            <button
              className="rounded-full p-2 text-gray-300 transition-colors hover:text-white"
              aria-label="Settings"
              type="button"
              onClick={() => openDrawer("settings")}
            >
              <Settings className="h-[22px] w-[22px]" />
            </button>
          </div>
        </div>

        <div
          className={`scrollbar-hide relative z-10 min-h-0 flex-1 px-5 ${
            isChatScreen
              ? "overflow-hidden pb-3 pt-3"
              : "overflow-y-auto overscroll-contain pb-28 pt-1"
          }`}
        >
          {screen === "dashboard" ? (
            <div className="space-y-4">
              <DashboardHero
                busyNote={busyNote}
                candidateCount={candidates.length}
                jobCount={jobs.length}
                selectedCandidateName={selectedCandidate?.personal.full_name ?? "None selected"}
                selectedJobTitle={selectedJob?.title ?? "None selected"}
                topMatchScore={ranking?.ranked_candidates[0]?.score ?? null}
              />
              <PageStatusAlerts errorMessage={errorMessage} busyNote={busyNote} />
              <SectionCard
                title="Quick actions"
                subtitle="Run the full workflow from mobile-first cards."
              >
                <div className="grid grid-cols-2 gap-3">
                  <ActionButton
                    icon={Plus}
                    title="Seed workspace"
                    description="Create a sample candidate and job."
                    onClick={() => void handleSeedWorkspace()}
                  />
                  <ActionButton
                    icon={Target}
                    title="Rank now"
                    description="Score candidates against the selected job."
                    onClick={() => void handleRankCandidates()}
                  />
                  <ActionButton
                    icon={FileJson}
                    title="Template JSON"
                    description="Generate template-ready resume data."
                    onClick={() => void handleGenerateTemplate()}
                  />
                  <ActionButton
                    icon={RefreshCcw}
                    title="Refresh"
                    description="Sync candidates and jobs from backend."
                    onClick={() => void refreshData()}
                  />
                </div>
              </SectionCard>

              <SectionCard
                title="Workspace health"
                subtitle="Current context for ranking, summaries, and recruiter chat."
              >
                <div className="space-y-3">
                  <SummaryRow label="Selected candidate" value={selectedCandidate?.personal.full_name ?? "No candidate selected"} />
                  <SummaryRow label="Selected job" value={selectedJob?.title ?? "No job selected"} />
                  <SummaryRow
                    label="Template preview"
                    value={
                      resumePreview
                        ? `${resumePreview.resume.sections.length} sections in ${resumePreview.resume.template_id}`
                        : "No template generated yet"
                    }
                  />
                </div>
              </SectionCard>

              {ranking?.ranked_candidates[0] ? (
                <SectionCard
                  title="Best current match"
                  subtitle={ranking.job_title}
                >
                  <MatchCard result={ranking.ranked_candidates[0]} compact />
                </SectionCard>
              ) : null}

              {resumePreview ? (
                <SectionCard
                  title="Latest template payload"
                  subtitle={`${resumePreview.resume.template_id} template`}
                >
                  <div className="space-y-2">
                    {resumePreview.resume.sections.slice(0, 4).map((section) => (
                      <div
                        key={`${section.type}-${section.key ?? "default"}`}
                        className="rounded-2xl border border-white/10 bg-white/[0.03] px-3 py-2"
                      >
                        <div className="text-[12px] font-medium text-white">
                          {section.title ?? section.type}
                        </div>
                        <div className="mt-1 text-[11px] text-gray-400">
                          {section.blocks.length} render block{section.blocks.length === 1 ? "" : "s"}
                        </div>
                      </div>
                    ))}
                  </div>
                </SectionCard>
              ) : null}
            </div>
          ) : null}

          {screen === "candidates" ? (
            <div className="space-y-4">
              <DashboardHero
                busyNote={busyNote}
                candidateCount={candidates.length}
                jobCount={jobs.length}
                selectedCandidateName={selectedCandidate?.personal.full_name ?? "None selected"}
                selectedJobTitle={selectedJob?.title ?? "None selected"}
                topMatchScore={ranking?.ranked_candidates[0]?.score ?? null}
              />
              <PageStatusAlerts errorMessage={errorMessage} busyNote={busyNote} />
              <SectionCard
                title="Add candidate"
                subtitle="Capture enough structured data for matching and resume generation."
              >
                <div className="space-y-3">
                  <LabeledInput
                    label="Full name"
                    value={candidateDraft.fullName}
                    onChange={(value) => setCandidateDraft((current) => ({ ...current, fullName: value }))}
                    placeholder="Ava Sharma"
                  />
                  <LabeledInput
                    label="Headline"
                    value={candidateDraft.headline}
                    onChange={(value) => setCandidateDraft((current) => ({ ...current, headline: value }))}
                    placeholder="Senior Python Backend Engineer"
                  />
                  <LabeledInput
                    label="Location"
                    value={candidateDraft.location}
                    onChange={(value) => setCandidateDraft((current) => ({ ...current, location: value }))}
                    placeholder="Bengaluru"
                  />
                  <LabeledTextarea
                    label="Summary"
                    value={candidateDraft.summary}
                    onChange={(value) => setCandidateDraft((current) => ({ ...current, summary: value }))}
                    placeholder="Backend engineer focused on recruiter workflows and AI products."
                  />
                  <LabeledInput
                    label="Skills"
                    value={candidateDraft.skills}
                    onChange={(value) => setCandidateDraft((current) => ({ ...current, skills: value }))}
                    placeholder="Python, FastAPI, REST APIs, Docker"
                  />
                  <div className="grid grid-cols-2 gap-3">
                    <LabeledInput
                      label="Current role"
                      value={candidateDraft.role}
                      onChange={(value) => setCandidateDraft((current) => ({ ...current, role: value }))}
                      placeholder="Senior Backend Engineer"
                    />
                    <LabeledInput
                      label="Company"
                      value={candidateDraft.company}
                      onChange={(value) => setCandidateDraft((current) => ({ ...current, company: value }))}
                      placeholder="TalentForge"
                    />
                  </div>
                  <LabeledInput
                    label="Years of experience"
                    value={candidateDraft.experienceYears}
                    onChange={(value) => setCandidateDraft((current) => ({ ...current, experienceYears: value }))}
                    placeholder="3"
                  />
                  <button
                    className="w-full rounded-2xl bg-gradient-to-r from-blue-500 to-fuchsia-500 px-4 py-3 text-[13px] font-medium text-white shadow-lg shadow-fuchsia-500/20"
                    type="button"
                    onClick={() => void handleCreateCandidate()}
                  >
                    Save candidate
                  </button>
                </div>
              </SectionCard>

              <SectionCard title="Candidate list" subtitle="Select a profile for chat, matching, and resume JSON.">
                <div className="space-y-3">
                  {candidates.length === 0 ? (
                    <EmptyState
                      title="No candidates yet"
                      body="Create a candidate or seed the workspace to start ranking."
                    />
                  ) : (
                    candidates.map((candidate) => (
                      <button
                        key={candidate.candidate_id}
                        className={`w-full rounded-2xl border px-4 py-3 text-left transition ${
                          selectedCandidateId === candidate.candidate_id
                            ? "border-cyan-400/40 bg-cyan-400/10"
                            : "border-white/10 bg-white/[0.03] hover:bg-white/[0.06]"
                        }`}
                        type="button"
                        onClick={() => setSelectedCandidateId(candidate.candidate_id)}
                      >
                        <div className="flex items-start justify-between gap-3">
                          <div>
                            <div className="text-[14px] font-medium text-white">
                              {candidate.personal.full_name}
                            </div>
                            <div className="mt-1 text-[11px] text-gray-400">
                              {candidate.personal.headline ?? "No headline"}
                            </div>
                          </div>
                          {selectedCandidateId === candidate.candidate_id ? (
                            <CheckCircle2 className="h-4 w-4 text-cyan-300" />
                          ) : null}
                        </div>
                        <div className="mt-3 flex flex-wrap gap-2">
                          {candidate.skills.flatMap((group) => group.items).slice(0, 4).map((skill) => (
                            <Chip key={`${candidate.candidate_id}-${skill.name}`}>{skill.name}</Chip>
                          ))}
                        </div>
                      </button>
                    ))
                  )}
                </div>
              </SectionCard>
            </div>
          ) : null}

          {screen === "jobs" ? (
            <div className="space-y-4">
              <DashboardHero
                busyNote={busyNote}
                candidateCount={candidates.length}
                jobCount={jobs.length}
                selectedCandidateName={selectedCandidate?.personal.full_name ?? "None selected"}
                selectedJobTitle={selectedJob?.title ?? "None selected"}
                topMatchScore={ranking?.ranked_candidates[0]?.score ?? null}
              />
              <PageStatusAlerts errorMessage={errorMessage} busyNote={busyNote} />
              <SectionCard
                title="Add job"
                subtitle="Save structured job requirements for deterministic ranking."
              >
                <div className="space-y-3">
                  <LabeledInput
                    label="Job title"
                    value={jobDraft.title}
                    onChange={(value) => setJobDraft((current) => ({ ...current, title: value }))}
                    placeholder="AI Recruitment Backend Engineer"
                  />
                  <div className="grid grid-cols-2 gap-3">
                    <LabeledInput
                      label="Company"
                      value={jobDraft.company}
                      onChange={(value) => setJobDraft((current) => ({ ...current, company: value }))}
                      placeholder="TalentFlow"
                    />
                    <LabeledInput
                      label="Location"
                      value={jobDraft.location}
                      onChange={(value) => setJobDraft((current) => ({ ...current, location: value }))}
                      placeholder="Remote"
                    />
                  </div>
                  <LabeledTextarea
                    label="Summary"
                    value={jobDraft.summary}
                    onChange={(value) => setJobDraft((current) => ({ ...current, summary: value }))}
                    placeholder="Build ranking and recruiter summary APIs."
                  />
                  <LabeledInput
                    label="Must-have skills"
                    value={jobDraft.mustHaveSkills}
                    onChange={(value) => setJobDraft((current) => ({ ...current, mustHaveSkills: value }))}
                    placeholder="Python, FastAPI, REST APIs"
                  />
                  <LabeledInput
                    label="Nice-to-have skills"
                    value={jobDraft.niceToHaveSkills}
                    onChange={(value) => setJobDraft((current) => ({ ...current, niceToHaveSkills: value }))}
                    placeholder="Docker, LLMs, Prompt Engineering"
                  />
                  <div className="grid grid-cols-2 gap-3">
                    <LabeledInput
                      label="Keywords"
                      value={jobDraft.keywords}
                      onChange={(value) => setJobDraft((current) => ({ ...current, keywords: value }))}
                      placeholder="matching, ranking, recruiter"
                    />
                    <LabeledInput
                      label="Minimum years"
                      value={jobDraft.minimumYears}
                      onChange={(value) => setJobDraft((current) => ({ ...current, minimumYears: value }))}
                      placeholder="3"
                    />
                  </div>
                  <label className="block">
                    <span className="mb-2 block text-[11px] uppercase tracking-[0.22em] text-gray-400">
                      Seniority
                    </span>
                    <select
                      value={jobDraft.seniority ?? "mid"}
                      onChange={(event) =>
                        setJobDraft((current) => ({
                          ...current,
                          seniority: event.target.value as JobDescription["seniority"],
                        }))
                      }
                      className="w-full rounded-2xl border border-white/10 bg-white/[0.03] px-4 py-3 text-[13px] text-white outline-none"
                    >
                      <option value="intern">Intern</option>
                      <option value="junior">Junior</option>
                      <option value="mid">Mid</option>
                      <option value="senior">Senior</option>
                      <option value="lead">Lead</option>
                      <option value="manager">Manager</option>
                    </select>
                  </label>
                  <button
                    className="w-full rounded-2xl bg-gradient-to-r from-cyan-500 to-blue-500 px-4 py-3 text-[13px] font-medium text-white shadow-lg shadow-cyan-500/20"
                    type="button"
                    onClick={() => void handleCreateJob()}
                  >
                    Save job
                  </button>
                </div>
              </SectionCard>

              <SectionCard title="Job list" subtitle="Select the role that will drive ranking and recruiter chat.">
                <div className="space-y-3">
                  {jobs.length === 0 ? (
                    <EmptyState
                      title="No jobs yet"
                      body="Add a role definition or seed the workspace to start matching."
                    />
                  ) : (
                    jobs.map((job) => (
                      <button
                        key={job.job_id}
                        className={`w-full rounded-2xl border px-4 py-3 text-left transition ${
                          selectedJobId === job.job_id
                            ? "border-fuchsia-400/40 bg-fuchsia-500/10"
                            : "border-white/10 bg-white/[0.03] hover:bg-white/[0.06]"
                        }`}
                        type="button"
                        onClick={() => setSelectedJobId(job.job_id)}
                      >
                        <div className="flex items-start justify-between gap-3">
                          <div>
                            <div className="text-[14px] font-medium text-white">{job.title}</div>
                            <div className="mt-1 text-[11px] text-gray-400">
                              {job.company ?? "No company"} {job.location ? `| ${job.location}` : ""}
                            </div>
                          </div>
                          {selectedJobId === job.job_id ? (
                            <CheckCircle2 className="h-4 w-4 text-fuchsia-300" />
                          ) : null}
                        </div>
                        <div className="mt-3 flex flex-wrap gap-2">
                          {job.must_have_skills.slice(0, 4).map((skill) => (
                            <Chip key={`${job.job_id}-${skill}`}>{skill}</Chip>
                          ))}
                        </div>
                      </button>
                    ))
                  )}
                </div>
              </SectionCard>
            </div>
          ) : null}

          {screen === "matches" ? (
            <div className="space-y-4">
              <DashboardHero
                busyNote={busyNote}
                candidateCount={candidates.length}
                jobCount={jobs.length}
                selectedCandidateName={selectedCandidate?.personal.full_name ?? "None selected"}
                selectedJobTitle={selectedJob?.title ?? "None selected"}
                topMatchScore={ranking?.ranked_candidates[0]?.score ?? null}
              />
              <PageStatusAlerts errorMessage={errorMessage} busyNote={busyNote} />
              <SectionCard title="Candidate ranking" subtitle="Deterministic matching with recruiter-ready summaries.">
                <div className="flex flex-col gap-3">
                  <SelectionSummary
                    title="Ranking context"
                    body={`${selectedJob?.title ?? "No job selected"} | ${candidates.length} candidates available`}
                  />
                  <button
                    className="w-full rounded-2xl bg-gradient-to-r from-fuchsia-500 to-blue-500 px-4 py-3 text-[13px] font-medium text-white shadow-lg shadow-fuchsia-500/20"
                    type="button"
                    onClick={() => void handleRankCandidates()}
                  >
                    Run ranking
                  </button>
                </div>
              </SectionCard>

              {ranking?.ranked_candidates.length ? (
                <SectionCard
                  title={`Results for ${ranking.job_title}`}
                  subtitle={`${ranking.total_candidates} candidates scored`}
                >
                  <div className="space-y-3">
                    {ranking.ranked_candidates.map((result, index) => (
                      <div key={`${result.candidate_id}-${index}`} className="space-y-3">
                        <MatchCard result={result} />
                      </div>
                    ))}
                  </div>
                </SectionCard>
              ) : (
                <SectionCard title="No ranking yet" subtitle="Use the selected job to score all saved candidates.">
                  <EmptyState
                    title="Ranking output appears here"
                    body="Once you run ranking, this screen shows scores, skill hits, gaps, and recruiter summaries."
                  />
                </SectionCard>
              )}
            </div>
          ) : null}

          {screen === "chat" ? (
            <div className="flex h-full min-h-0 flex-col">
              <div className="scrollbar-hide min-h-0 flex-1 overflow-y-auto overscroll-contain pb-4">
                <div className="flex min-h-full flex-col justify-end gap-3">
                  <ChatContextCard
                    activeTool={activeTool}
                    busyNote={busyNote}
                    selectedCandidateName={selectedCandidate?.personal.full_name ?? "No candidate"}
                    selectedJobTitle={selectedJob?.title ?? "No job"}
                  />
                  {toolRequirementNote ? (
                    <div className="rounded-2xl border border-amber-400/20 bg-amber-400/10 px-4 py-3 text-[12px] text-amber-100">
                      {toolRequirementNote}
                    </div>
                  ) : null}

                  {toolExecutionHint ? (
                    <div className="rounded-2xl border border-white/8 bg-white/[0.03] px-4 py-3 text-[12px] text-gray-300">
                      {toolExecutionHint}
                    </div>
                  ) : null}

                  {errorMessage ? (
                    <div className="rounded-2xl border border-red-500/30 bg-red-500/10 px-4 py-3 text-[12px] text-red-100">
                      {errorMessage}
                    </div>
                  ) : null}

                  {messages.map((message) => (
                    <div
                      key={message.id}
                      className={`flex ${message.role === "user" ? "justify-end" : "justify-start"}`}
                    >
                      <div className="max-w-[88%]">
                        {message.role === "user" ? (
                          <div className="rounded-2xl bg-gradient-to-r from-blue-500 to-fuchsia-500 px-4 py-2 text-white shadow-lg shadow-fuchsia-500/10">
                            <p className="whitespace-pre-wrap break-words text-[13px] leading-relaxed">
                              {message.text}
                            </p>
                            {message.files?.length ? (
                              <div className="mt-2 border-t border-white/15 pt-2 text-[11px] text-white/90">
                                {message.files.join(", ")}
                              </div>
                            ) : null}
                          </div>
                        ) : (
                          <div className="singulyn-answer-frame relative rounded-2xl p-[1px]">
                            <div className="relative z-10 rounded-2xl border border-white/10 bg-[#05050A]/75 px-4 py-2 text-gray-100">
                              <p className="whitespace-pre-wrap break-words text-[13px] leading-relaxed">
                                {message.text}
                              </p>
                            </div>
                          </div>
                        )}
                        <div
                          className={`mt-1 text-[9px] text-gray-500 ${
                            message.role === "user" ? "text-right" : "text-left"
                          }`}
                        >
                          {new Date(message.timestamp).toLocaleTimeString([], {
                            hour: "2-digit",
                            minute: "2-digit",
                          })}
                        </div>
                      </div>
                    </div>
                  ))}

                  {assistantStatus !== "idle" ? (
                    <div className="flex justify-start">
                      <div className="max-w-[85%]">
                        <div className="singulyn-flow-frame singulyn-flow-frame--active relative rounded-2xl p-[1px]">
                          <div className="relative z-10 rounded-2xl border border-white/10 bg-[#05050A]/75 px-4 py-3">
                            <NeonProcessingIndicator
                              label={getStatusLabel(assistantStatus, activeTool)}
                              mode={assistantStatus}
                            />
                          </div>
                        </div>
                      </div>
                    </div>
                  ) : null}
                  <div ref={messagesEndRef} />
                </div>
              </div>

              <div className="shrink-0 pb-2 pt-2">
                {attachments.length ? (
                  <div className="mb-2 flex flex-wrap gap-2">
                    {attachments.map((file, index) => (
                      <div
                        key={`${file.name}-${file.lastModified}`}
                        className="flex items-center gap-2 rounded-full border border-white/10 bg-white/5 px-3 py-1.5"
                      >
                        <span className="max-w-[220px] truncate text-[11px] text-gray-200">
                          {file.name}
                        </span>
                        <button
                          className="text-gray-400 transition-colors hover:text-white"
                          type="button"
                          onClick={() => removeAttachment(index)}
                        >
                          x
                        </button>
                      </div>
                    ))}
                  </div>
                ) : null}

                <div className="mb-2 flex items-center justify-between px-1 text-[11px] text-gray-500">
                  <span className="truncate">{getToolPlaceholder(activeTool)}</span>
                  <span className="ml-3 shrink-0 uppercase tracking-[0.18em] text-cyan-200/80">
                    {activeTool === "Recruitment Assistant" ? "Type prompt" : "Tap send"}
                  </span>
                </div>

                <div className="relative flex items-center gap-2 rounded-[28px] border border-white/10 bg-[#0a0a14]/60 p-2 shadow-lg backdrop-blur-xl">
                  <button
                    className="rounded-full bg-white/5 p-2.5 text-gray-300 transition-colors active:scale-95 hover:bg-white/10"
                    aria-label="Add attachment"
                    type="button"
                    onClick={handleAddAttachmentClick}
                  >
                    <Plus className="h-[18px] w-[18px]" />
                  </button>

                  <input
                    type="text"
                    placeholder={getToolPlaceholder(activeTool)}
                    value={draft}
                    onChange={(event) => setDraft(event.target.value)}
                    onKeyDown={handleKeyDown}
                    className="min-w-0 flex-1 bg-transparent text-[13px] text-white placeholder-gray-500 outline-none"
                  />

                  <input
                    ref={fileInputRef}
                    type="file"
                    className="hidden"
                    multiple
                    onChange={handleFileChange}
                  />

                  <div className="flex items-center gap-2">
                    <button
                      className={`rounded-full p-2.5 text-white shadow-lg shadow-fuchsia-500/20 transition-all active:scale-95 ${
                        canSend
                          ? "bg-gradient-to-r from-blue-500 to-fuchsia-500"
                          : "cursor-not-allowed bg-white/10 text-gray-500"
                      }`}
                      aria-label="Send"
                      type="button"
                      disabled={!canSend}
                      onClick={() => void handleSend()}
                    >
                      <Send className="ml-0.5 h-[18px] w-[18px]" />
                    </button>
                  </div>
                </div>
              </div>
            </div>
          ) : null}
        </div>

        <div className="relative z-20 shrink-0 border-t border-white/5 bg-[#020206]/80 px-5 pb-[calc(env(safe-area-inset-bottom)+16px)] pt-3 backdrop-blur-2xl">
          <div className="flex items-center justify-between gap-1">
            <NavItem
              icon={Home}
              label="Home"
              active={screen === "dashboard"}
              onClick={() => setScreen("dashboard")}
            />
            <NavItem
              icon={Users}
              label="People"
              active={screen === "candidates"}
              onClick={() => setScreen("candidates")}
            />
            <NavItem
              icon={Briefcase}
              label="Jobs"
              active={screen === "jobs"}
              onClick={() => setScreen("jobs")}
            />
            <NavItem
              icon={Trophy}
              label="Matches"
              active={screen === "matches"}
              onClick={() => setScreen("matches")}
            />
            <NavItem
              icon={MessageSquare}
              label="Chat"
              active={screen === "chat"}
              onClick={() => setScreen("chat")}
            />
          </div>
          <div className="mx-auto mt-4 h-1 w-28 rounded-full bg-white/80" />
        </div>
      </div>

      <div
        className={`fixed inset-0 z-40 bg-black/60 backdrop-blur-sm transition-opacity duration-300 ${
          isDrawerOpen ? "opacity-100" : "pointer-events-none opacity-0"
        }`}
        onClick={closeDrawer}
      />

      <div
        className={`fixed left-0 top-0 z-50 flex h-full w-[85%] max-w-[320px] flex-col border-r border-white/10 bg-[#05050A]/95 backdrop-blur-3xl transition-transform duration-[400ms] ease-[cubic-bezier(0.16,1,0.3,1)] ${
          isDrawerOpen ? "translate-x-0" : "-translate-x-full"
        }`}
      >
        {drawerView === "menu" ? (
          <>
            <div className="flex items-center justify-between px-6 pb-6 pt-[calc(env(safe-area-inset-top)+20px)]">
              <div className="flex items-center space-x-3">
                <div className="relative">
                  <div className="flex h-12 w-12 items-center justify-center rounded-full bg-gradient-to-br from-blue-500 to-fuchsia-600 text-lg font-semibold text-white shadow-lg">
                    RA
                  </div>
                  <div className="absolute bottom-0 right-0 h-3.5 w-3.5 rounded-full border-2 border-[#05050A] bg-green-400" />
                </div>
                <div className="flex flex-col">
                  <span className="text-[14px] font-medium text-white">Recruitment Console</span>
                  <span className="text-xs text-gray-400">Local-first, mobile-first</span>
                </div>
              </div>
              <button
                className="text-gray-300"
                aria-label="Settings"
                type="button"
                onClick={() => openDrawer("settings")}
              >
                <Settings className="h-4 w-4" />
              </button>
            </div>

            <div className="scrollbar-hide flex-1 overflow-y-auto px-6 pb-24">
              <div className="mb-8">
                <p className="mb-4 text-[11px] font-semibold uppercase tracking-wider text-gray-500">
                  AI Tools
                </p>
                <div className="space-y-1">
                  <DrawerItem
                    icon={MessageSquare}
                    label="Recruitment Assistant"
                    active={activeTool === "Recruitment Assistant"}
                    onClick={() => {
                      setActiveTool("Recruitment Assistant");
                      setScreen("chat");
                      closeDrawer();
                    }}
                  />
                  <DrawerItem
                    icon={FileText}
                    label="Resume Summary"
                    active={activeTool === "Resume Summary"}
                    onClick={() => {
                      setActiveTool("Resume Summary");
                      setScreen("chat");
                      closeDrawer();
                    }}
                  />
                  <DrawerItem
                    icon={Target}
                    label="Candidate Ranking"
                    active={activeTool === "Candidate Ranking"}
                    onClick={() => {
                      setActiveTool("Candidate Ranking");
                      setScreen("chat");
                      closeDrawer();
                    }}
                  />
                  <DrawerItem
                    icon={BrainCircuit}
                    label="Recruiter Notes"
                    active={activeTool === "Recruiter Notes"}
                    onClick={() => {
                      setActiveTool("Recruiter Notes");
                      setScreen("chat");
                      closeDrawer();
                    }}
                  />
                  <DrawerItem
                    icon={FileJson}
                    label="Template JSON"
                    active={activeTool === "Template JSON"}
                    onClick={() => {
                      setActiveTool("Template JSON");
                      setScreen("chat");
                      closeDrawer();
                    }}
                  />
                </div>
              </div>

              <div className="mb-6 h-px w-full bg-white/5" />

              <div className="mb-6">
                <p className="mb-4 text-[11px] font-semibold uppercase tracking-wider text-gray-500">
                  Workspace
                </p>
                <div className="space-y-1">
                  <DrawerItem
                    icon={Home}
                    label="Dashboard"
                    active={screen === "dashboard"}
                    onClick={() => {
                      setScreen("dashboard");
                      closeDrawer();
                    }}
                  />
                  <DrawerItem
                    icon={Users}
                    label="Candidates"
                    active={screen === "candidates"}
                    onClick={() => {
                      setScreen("candidates");
                      closeDrawer();
                    }}
                  />
                  <DrawerItem
                    icon={Briefcase}
                    label="Jobs"
                    active={screen === "jobs"}
                    onClick={() => {
                      setScreen("jobs");
                      closeDrawer();
                    }}
                  />
                  <DrawerItem
                    icon={Trophy}
                    label="Matches"
                    active={screen === "matches"}
                    onClick={() => {
                      setScreen("matches");
                      closeDrawer();
                    }}
                  />
                  <DrawerItem
                    icon={MessageSquare}
                    label="Chat"
                    active={screen === "chat"}
                    onClick={() => {
                      setScreen("chat");
                      closeDrawer();
                    }}
                  />
                </div>
              </div>

              <div className="mb-6">
                <p className="mb-4 text-[11px] font-semibold uppercase tracking-wider text-gray-500">
                  Quick controls
                </p>
                <div className="space-y-1">
                  <DrawerItem
                    icon={Plus}
                    label="Seed sample data"
                    onClick={() => {
                      void handleSeedWorkspace();
                      closeDrawer();
                    }}
                  />
                  <DrawerItem
                    icon={RefreshCcw}
                    label="Refresh data"
                    onClick={() => {
                      void refreshData();
                      closeDrawer();
                    }}
                  />
                  <DrawerItem
                    icon={Bookmark}
                    label="Generate template"
                    onClick={() => {
                      void handleGenerateTemplate();
                      closeDrawer();
                    }}
                  />
                  <DrawerItem
                    icon={Clock3}
                    label="New chat thread"
                    onClick={() => {
                      resetChat();
                      setScreen("chat");
                      closeDrawer();
                    }}
                  />
                </div>
              </div>

              <button
                className="mt-2 flex w-full items-center space-x-3 rounded-xl border border-red-500/30 p-3 text-red-400 transition-colors active:scale-[0.99] hover:bg-red-500/10"
                type="button"
                onClick={() => {
                  setScreen("dashboard");
                  setActiveTool("Recruitment Assistant");
                  resetChat();
                  closeDrawer();
                }}
              >
                <LogOut className="h-[18px] w-[18px]" />
                <span className="text-[13px] font-medium">Reset session</span>
              </button>

              <div className="mb-4 mt-8 flex items-center justify-center space-x-1 text-[10px] text-gray-600">
                <span>v1.0</span>
                <span>|</span>
                <span>FastAPI + Next.js</span>
                <Sparkles className="h-3 w-3" />
              </div>
            </div>
          </>
        ) : drawerView === "notifications" ? (
          <>
            <DrawerTitleBar title="Notifications" onBack={() => setDrawerView("menu")} />
            <div className="scrollbar-hide flex-1 overflow-y-auto px-6 pb-10 pt-4">
              {notifications.length === 0 ? (
                <div className="text-[13px] text-gray-400">No notifications yet.</div>
              ) : (
                <div className="space-y-3">
                  {notifications.map((item) => (
                    <button
                      key={item.id}
                      className="w-full rounded-2xl border border-white/10 bg-white/5 p-4 text-left transition-colors hover:bg-white/10"
                      type="button"
                      onClick={() =>
                        setNotifications((current) =>
                          current.map((notification) =>
                            notification.id === item.id
                              ? { ...notification, unread: false }
                              : notification,
                          ),
                        )
                      }
                    >
                      <div className="flex items-start justify-between gap-3">
                        <div className="flex items-center gap-2">
                          <span className="text-[13px] font-medium text-white">{item.title}</span>
                          {item.unread ? (
                            <span className="h-1.5 w-1.5 rounded-full bg-fuchsia-500" />
                          ) : null}
                        </div>
                        <span className="text-[10px] text-gray-500">
                          {new Date(item.timestamp).toLocaleTimeString([], {
                            hour: "2-digit",
                            minute: "2-digit",
                          })}
                        </span>
                      </div>
                      <p className="mt-2 text-[11px] leading-relaxed text-gray-400">{item.body}</p>
                    </button>
                  ))}
                </div>
              )}
            </div>
          </>
        ) : (
          <>
            <DrawerTitleBar title="Settings" onBack={() => setDrawerView("menu")} />
            <div className="scrollbar-hide flex-1 overflow-y-auto px-6 pb-10 pt-4">
              <div className="space-y-4">
                <SettingToggle
                  label="Enter to send"
                  description="Press Enter to send chat messages."
                  value={enterToSend}
                  onToggle={() => setEnterToSend((current) => !current)}
                />

                <button
                  className="flex w-full items-center justify-between rounded-2xl border border-white/10 bg-white/5 p-4 transition-colors hover:bg-white/10"
                  type="button"
                  onClick={() => {
                    resetChat();
                    closeDrawer();
                  }}
                >
                  <span className="text-[13px] font-medium text-white">Clear chat</span>
                  <span className="text-[11px] text-gray-500">Reset</span>
                </button>

                <button
                  className="flex w-full items-center justify-between rounded-2xl border border-white/10 bg-white/5 p-4 transition-colors hover:bg-white/10"
                  type="button"
                  onClick={() => void refreshData()}
                >
                  <span className="text-[13px] font-medium text-white">Reload backend data</span>
                  <span className="text-[11px] text-gray-500">Sync</span>
                </button>

                <div className="pt-2 text-[11px] text-gray-500">
                  Theme: neon dark | Mode: mobile workspace | Deploy target: Coolify
                </div>
              </div>
            </div>
          </>
        )}
      </div>
    </div>
  );
}

function DashboardHero({
  busyNote,
  candidateCount,
  jobCount,
  selectedCandidateName,
  selectedJobTitle,
  topMatchScore,
}: {
  busyNote: string | null;
  candidateCount: number;
  jobCount: number;
  selectedCandidateName: string;
  selectedJobTitle: string;
  topMatchScore: number | null;
}) {
  return (
    <div className="rounded-[24px] border border-white/10 bg-white/[0.03] p-4 backdrop-blur-xl">
      <div className="flex items-start justify-between gap-3">
        <div>
          <p className="text-[11px] uppercase tracking-[0.24em] text-cyan-300/80">
            AI Recruitment Assistant
          </p>
          <h1 className="mt-2 text-[22px] font-semibold leading-tight">
            Mobile control room for hiring workflows
          </h1>
        </div>
        <div className="rounded-2xl border border-cyan-400/20 bg-cyan-400/10 px-3 py-2 text-right">
          <p className="text-[10px] uppercase tracking-[0.22em] text-cyan-200">Status</p>
          <p className="mt-1 text-[13px] font-medium text-white">
            {busyNote ? "Working" : "Ready"}
          </p>
        </div>
      </div>

      <div className="mt-4 grid grid-cols-3 gap-2">
        <MetricCard label="Candidates" value={String(candidateCount)} icon={Users} />
        <MetricCard label="Jobs" value={String(jobCount)} icon={Briefcase} />
        <MetricCard
          label="Top Match"
          value={topMatchScore ? `${topMatchScore}%` : "--"}
          icon={Trophy}
        />
      </div>

      <div className="mt-4 flex flex-wrap gap-2">
        <ContextPill title="Candidate" value={selectedCandidateName} />
        <ContextPill title="Job" value={selectedJobTitle} />
      </div>
    </div>
  );
}

function ChatContextCard({
  activeTool,
  busyNote,
  selectedCandidateName,
  selectedJobTitle,
}: {
  activeTool: Tool;
  busyNote: string | null;
  selectedCandidateName: string;
  selectedJobTitle: string;
}) {
  return (
    <div className="flex items-center justify-between gap-3 rounded-full border border-white/10 bg-white/[0.03] px-4 py-2.5 backdrop-blur-xl">
      <div className="min-w-0">
        <p className="text-[10px] uppercase tracking-[0.24em] text-cyan-300/80">Chat</p>
        <p className="truncate text-[13px] font-medium text-white">{activeTool}</p>
      </div>
      <div className="min-w-0 text-right">
        <div className="text-[10px] uppercase tracking-[0.18em] text-gray-500">
          {busyNote ? "Busy" : "Live"}
        </div>
        <div className="truncate text-[11px] text-gray-300">
          {selectedCandidateName} / {selectedJobTitle}
        </div>
      </div>
    </div>
  );
}

function PageStatusAlerts({
  errorMessage,
  busyNote,
}: {
  errorMessage: string | null;
  busyNote: string | null;
}) {
  if (!errorMessage && !busyNote) {
    return null;
  }

  return (
    <div className="space-y-3">
      {errorMessage ? (
        <div className="rounded-2xl border border-red-500/30 bg-red-500/10 px-4 py-3 text-[12px] text-red-100">
          {errorMessage}
        </div>
      ) : null}

      {busyNote ? (
        <div className="rounded-2xl border border-white/10 bg-white/[0.04] px-4 py-3">
          <NeonProcessingIndicator label={busyNote} mode="processing" />
        </div>
      ) : null}
    </div>
  );
}

function NeonProcessingIndicator({
  label,
  mode,
}: {
  label: string;
  mode: Exclude<AssistantStatus, "idle">;
}) {
  return (
    <div className="flex items-center justify-between gap-4">
      <div className="min-w-0">
        <div className="text-[12px] font-medium tracking-wide text-gray-100">{label}...</div>
        <div className="mt-1 text-[10px] uppercase tracking-[0.22em] text-gray-500">
          {mode === "processing"
            ? "Deterministic pipeline"
            : mode === "generating"
              ? "LLM generation"
              : "Prompt reasoning"}
        </div>
      </div>
      <div className={`singulyn-activity singulyn-activity--${mode}`} aria-label={`${label} animation`}>
        <span className="singulyn-activity__bar" />
        <span className="singulyn-activity__bar" />
        <span className="singulyn-activity__bar" />
        <span className="singulyn-activity__bar" />
        <span className="singulyn-activity__core" />
      </div>
    </div>
  );
}

function MetricCard({
  label,
  value,
  icon: Icon,
}: {
  label: string;
  value: string;
  icon: LucideIcon;
}) {
  return (
    <div className="rounded-2xl border border-white/10 bg-white/[0.03] px-3 py-3">
      <div className="flex items-center justify-between">
        <span className="text-[10px] uppercase tracking-[0.22em] text-gray-400">{label}</span>
        <Icon className="h-4 w-4 text-cyan-300" />
      </div>
      <div className="mt-3 text-[18px] font-semibold text-white">{value}</div>
    </div>
  );
}

function ContextPill({ title, value }: { title: string; value: string }) {
  return (
    <div className="rounded-full border border-white/10 bg-white/[0.03] px-3 py-2">
      <span className="text-[10px] uppercase tracking-[0.2em] text-gray-500">{title}</span>
      <div className="mt-1 max-w-[180px] truncate text-[12px] text-white">{value}</div>
    </div>
  );
}

function SectionCard({
  title,
  subtitle,
  children,
}: {
  title: string;
  subtitle?: string;
  children: ReactNode;
}) {
  return (
    <div className="rounded-[24px] border border-white/10 bg-white/[0.03] p-4 backdrop-blur-xl">
      <div className="mb-4">
        <div className="text-[16px] font-semibold text-white">{title}</div>
        {subtitle ? <div className="mt-1 text-[12px] text-gray-400">{subtitle}</div> : null}
      </div>
      {children}
    </div>
  );
}

function ActionButton({
  icon: Icon,
  title,
  description,
  onClick,
}: {
  icon: LucideIcon;
  title: string;
  description: string;
  onClick: () => void;
}) {
  return (
    <button
      className="rounded-2xl border border-white/10 bg-white/[0.03] p-4 text-left transition hover:bg-white/[0.06]"
      type="button"
      onClick={onClick}
    >
      <Icon className="h-5 w-5 text-cyan-300" />
      <div className="mt-3 text-[13px] font-medium text-white">{title}</div>
      <div className="mt-1 text-[11px] leading-relaxed text-gray-400">{description}</div>
    </button>
  );
}

function SummaryRow({ label, value }: { label: string; value: string }) {
  return (
    <div className="flex items-start justify-between gap-3 rounded-2xl border border-white/10 bg-white/[0.03] px-3 py-3">
      <span className="text-[11px] uppercase tracking-[0.22em] text-gray-500">{label}</span>
      <span className="max-w-[60%] text-right text-[12px] text-white">{value}</span>
    </div>
  );
}

function SelectionSummary({ title, body }: { title: string; body: string }) {
  return (
    <div className="rounded-2xl border border-white/10 bg-white/[0.03] px-4 py-3">
      <div className="text-[11px] uppercase tracking-[0.22em] text-gray-500">{title}</div>
      <div className="mt-1 text-[12px] text-white">{body}</div>
    </div>
  );
}

function MatchCard({ result, compact = false }: { result: CandidateMatchResult; compact?: boolean }) {
  return (
    <div className="rounded-2xl border border-white/10 bg-white/[0.03] p-4">
      <div className="flex items-start justify-between gap-3">
        <div>
          <div className="text-[14px] font-medium text-white">{result.candidate_name}</div>
          <div className="mt-1 text-[11px] uppercase tracking-[0.18em] text-gray-500">
            {result.band} fit
          </div>
        </div>
        <div className="rounded-2xl border border-cyan-400/20 bg-cyan-400/10 px-3 py-2 text-right">
          <div className="text-[10px] uppercase tracking-[0.18em] text-cyan-200">Score</div>
          <div className="mt-1 text-[16px] font-semibold text-white">{result.score}%</div>
        </div>
      </div>

      <div className="mt-3 grid grid-cols-2 gap-2">
        <ScorePill label="Skills" value={result.breakdown.skill_score} />
        <ScorePill label="Keywords" value={result.breakdown.keyword_score} />
        {!compact ? <ScorePill label="Experience" value={result.breakdown.experience_score} /> : null}
        {!compact ? <ScorePill label="Seniority" value={result.breakdown.seniority_score} /> : null}
      </div>

      <div className="mt-3 flex flex-wrap gap-2">
        {result.matched_skills.slice(0, compact ? 3 : 6).map((skill) => (
          <Chip key={`${result.candidate_id}-${skill}`}>{skill}</Chip>
        ))}
      </div>

      {!compact && result.recruiter_summary ? (
        <p className="mt-3 text-[12px] leading-relaxed text-gray-300">{result.recruiter_summary}</p>
      ) : null}

      {!compact && result.missing_skills.length ? (
        <div className="mt-3 text-[11px] text-amber-200/90">
          Gaps: {result.missing_skills.slice(0, 4).join(", ")}
        </div>
      ) : null}
    </div>
  );
}

function ScorePill({ label, value }: { label: string; value: number }) {
  return (
    <div className="rounded-2xl border border-white/10 bg-[#090913] px-3 py-2">
      <div className="text-[10px] uppercase tracking-[0.18em] text-gray-500">{label}</div>
      <div className="mt-1 text-[13px] font-medium text-white">{Math.round(value)}%</div>
    </div>
  );
}

function EmptyState({ title, body }: { title: string; body: string }) {
  return (
    <div className="rounded-2xl border border-dashed border-white/10 bg-white/[0.02] px-4 py-5 text-center">
      <div className="text-[13px] font-medium text-white">{title}</div>
      <div className="mt-2 text-[11px] leading-relaxed text-gray-400">{body}</div>
    </div>
  );
}

function Chip({ children }: { children: ReactNode }) {
  return (
    <span className="rounded-full border border-white/10 bg-white/[0.03] px-3 py-1 text-[10px] uppercase tracking-[0.16em] text-cyan-100">
      {children}
    </span>
  );
}

function NavItem({
  icon: Icon,
  label,
  active,
  onClick,
}: {
  icon: LucideIcon;
  label: string;
  active: boolean;
  onClick: () => void;
}) {
  return (
    <button
      className="group relative flex w-16 flex-col items-center space-y-1"
      type="button"
      onClick={onClick}
    >
      <div className={active ? "text-cyan-400" : "text-gray-500 transition-colors group-hover:text-gray-300"}>
        <Icon className="h-[22px] w-[22px]" />
      </div>
      <span
        className={`text-[10px] font-medium ${
          active ? "text-cyan-400" : "text-gray-500 transition-colors group-hover:text-gray-300"
        }`}
      >
        {label}
      </span>
      {active ? <div className="absolute -bottom-2 h-1 w-1 rounded-full bg-cyan-400 shadow-[0_0_8px_#00E5FF]" /> : null}
    </button>
  );
}

function DrawerItem({
  icon: Icon,
  label,
  active = false,
  onClick,
}: {
  icon: LucideIcon;
  label: string;
  active?: boolean;
  onClick: () => void;
}) {
  return (
    <button
      className={`flex w-full items-center space-x-4 rounded-xl p-3 transition-all ${
        active ? "bg-white/10 text-white" : "text-gray-300 hover:bg-white/5 hover:text-white"
      }`}
      type="button"
      onClick={onClick}
    >
      <Icon className="h-[18px] w-[18px]" />
      <span className="text-[13px] font-medium tracking-wide">{label}</span>
    </button>
  );
}

function DrawerTitleBar({ title, onBack }: { title: string; onBack: () => void }) {
  return (
    <div className="flex items-center justify-between border-b border-white/5 px-6 pb-6 pt-[calc(env(safe-area-inset-top)+56px)]">
      <button
        className="-ml-2 p-2 text-gray-300 transition-colors hover:text-white"
        type="button"
        onClick={onBack}
        aria-label="Back"
      >
        <ChevronDown className="-rotate-90 h-[18px] w-[18px]" />
      </button>
      <span className="text-[14px] font-medium text-white">{title}</span>
      <div className="w-9" />
    </div>
  );
}

function SettingToggle({
  label,
  description,
  value,
  onToggle,
}: {
  label: string;
  description: string;
  value: boolean;
  onToggle: () => void;
}) {
  return (
    <button
      className="flex w-full items-center justify-between rounded-2xl border border-white/10 bg-white/5 p-4 transition-colors hover:bg-white/10"
      type="button"
      onClick={onToggle}
    >
      <div className="flex flex-col text-left">
        <span className="text-[13px] font-medium text-white">{label}</span>
        <span className="mt-1 text-[11px] text-gray-500">{description}</span>
      </div>
      <div
        className={`flex h-6 w-11 items-center rounded-full p-1 transition-colors ${
          value ? "bg-cyan-400/30" : "bg-white/10"
        }`}
      >
        <div
          className={`h-4 w-4 rounded-full transition-transform ${
            value ? "translate-x-5 bg-cyan-400" : "translate-x-0 bg-gray-400"
          }`}
        />
      </div>
    </button>
  );
}

function LabeledInput({
  label,
  value,
  onChange,
  placeholder,
}: {
  label: string;
  value: string;
  onChange: (value: string) => void;
  placeholder: string;
}) {
  return (
    <label className="block">
      <span className="mb-2 block text-[11px] uppercase tracking-[0.22em] text-gray-400">{label}</span>
      <input
        value={value}
        onChange={(event) => onChange(event.target.value)}
        placeholder={placeholder}
        className="w-full rounded-2xl border border-white/10 bg-white/[0.03] px-4 py-3 text-[13px] text-white outline-none placeholder:text-gray-500"
      />
    </label>
  );
}

function LabeledTextarea({
  label,
  value,
  onChange,
  placeholder,
}: {
  label: string;
  value: string;
  onChange: (value: string) => void;
  placeholder: string;
}) {
  return (
    <label className="block">
      <span className="mb-2 block text-[11px] uppercase tracking-[0.22em] text-gray-400">{label}</span>
      <textarea
        value={value}
        onChange={(event) => onChange(event.target.value)}
        placeholder={placeholder}
        rows={4}
        className="w-full rounded-2xl border border-white/10 bg-white/[0.03] px-4 py-3 text-[13px] text-white outline-none placeholder:text-gray-500"
      />
    </label>
  );
}
