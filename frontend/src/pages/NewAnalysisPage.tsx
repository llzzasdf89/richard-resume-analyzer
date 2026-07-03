import { useEffect, useRef, useState } from "react";
import {
  ArrowRight,
  CheckCircle2,
  Clock3,
  Loader2,
  Upload,
} from "lucide-react";

import {
  type AnalysisEvent,
  type AnalysisResult,
  createAnalysis,
  streamAnalysisEvents,
} from "@/api/analyses";
import { Header } from "@/components/resume-analyzer/Header";
import { ResultsPanel } from "@/components/resume-analyzer/ResultsPanel";
import { WorkflowPanel } from "@/components/resume-analyzer/WorkflowPanel";
import { Button } from "@/components/ui/button";
import { Card } from "@/components/ui/card";
import { Progress } from "@/components/ui/progress";
import { createRequestId } from "@/lib/requestId";

type AnalysisPhase = "upload" | "job" | "processing" | "results";
type StepStatus = "waiting" | "running" | "done" | "skipped";

const workflowSteps = [
  { step: "parsing", label: "Extract Resume" },
  { step: "jd_analysis", label: "JD Analysis" },
  { step: "rag_retrieval", label: "RAG Retrieval" },
  { step: "match_analysis", label: "Match Analysis" },
  { step: "supervisor", label: "Supervisor Routing" },
  { step: "skill_gap_agent", label: "Skill Gap Agent" },
  { step: "expression_agent", label: "Expression Agent" },
  { step: "strategy_agent", label: "Strategy Agent" },
  { step: "aggregate_suggestions", label: "Aggregate Suggestions" },
  { step: "rewrite", label: "Resume Rewrite" },
];
const supervisorBranchSteps = new Set([
  "supervisor",
  "skill_gap_agent",
  "expression_agent",
  "strategy_agent",
  "aggregate_suggestions",
]);
const skippedWhenAgentsBypassed = new Set([
  "supervisor",
  "skill_gap_agent",
  "expression_agent",
  "strategy_agent",
  "aggregate_suggestions",
]);

export function NewAnalysisPage() {
  const [phase, setPhase] = useState<AnalysisPhase>("upload");
  const [resume, setResume] = useState<File | null>(null);
  const [jobTitle, setJobTitle] = useState("");
  const [company, setCompany] = useState("");
  const [jdText, setJdText] = useState("");
  const [progress, setProgress] = useState(0);
  const [startedAt, setStartedAt] = useState<number | null>(null);
  const [error, setError] = useState("");
  const [stepStatus, setStepStatus] = useState<Record<string, StepStatus>>(() =>
    createInitialStepStatus(),
  );
  const [hiddenSteps, setHiddenSteps] = useState<Set<string>>(() =>
    createInitialHiddenSteps(),
  );
  const [analysisResult, setAnalysisResult] = useState<AnalysisResult | null>(
    null,
  );
  const abortRef = useRef<AbortController | null>(null);

  useEffect(() => {
    return () => abortRef.current?.abort();
  }, []);

  const start = async () => {
    if (!resume || !jdText.trim()) return;
    setError("");
    setPhase("processing");
    setProgress(0);
    setStartedAt(Date.now());
    setStepStatus(createInitialStepStatus());
    setHiddenSteps(createInitialHiddenSteps());
    setAnalysisResult(null);
    abortRef.current?.abort();
    const abortController = new AbortController();
    abortRef.current = abortController;

    try {
      const created = await createAnalysis(
        {
          resume,
          jdText,
          jobTitle: jobTitle.trim() || undefined,
          company: company.trim() || undefined,
        },
        createRequestId(),
      );
      await streamAnalysisEvents(
        created.analysis_id,
        handleAnalysisEvent,
        abortController.signal,
      );
    } catch (err) {
      if (abortController.signal.aborted) return;
      setError(err instanceof Error ? err.message : "Analysis failed");
      setPhase("job");
    }
  };

  const handleAnalysisEvent = (event: AnalysisEvent) => {
    if (typeof event.progress === "number") {
      setProgress(event.progress);
    }

    const eventStep = normalizeWorkflowStep(event.step);

    if (eventStep) {
      if (supervisorBranchSteps.has(eventStep)) {
        setHiddenSteps((current) => {
          const next = new Set(current);
          for (const step of supervisorBranchSteps) {
            next.delete(step);
          }
          return next;
        });
      } else if (eventStep === "rewrite") {
        setHiddenSteps(
          (current) => new Set([...current, ...supervisorBranchSteps]),
        );
      }
      setStepStatus((current) =>
        updateStepStatuses(
          current,
          eventStep,
          event.status === "completed" ? "done" : "running",
        ),
      );
    }

    if (event.type === "step" && eventStep) {
      setStepStatus((current) =>
        updateStepStatuses(current, eventStep, "done"),
      );
    }

    if (event.type === "completed") {
      setProgress(100);
      setStartedAt(null);
      setAnalysisResult(event.result ?? { score: event.score });
      if (event.result?.steps) {
        const ranSteps = new Set(
          event.result.steps
            .map(({ step }) => normalizeWorkflowStep(step))
            .filter(Boolean),
        );
        if (![...supervisorBranchSteps].some((step) => ranSteps.has(step))) {
          setHiddenSteps(
            (current) => new Set([...current, ...supervisorBranchSteps]),
          );
        }
        setStepStatus((current) => markCompletedResultSteps(current, ranSteps));
      } else {
        setStepStatus((current) => markUnfinishedStepsSkipped(current));
      }
      setPhase("results");
    }

    if (event.type === "failed") {
      setStartedAt(null);
      throw new Error(event.message || "Analysis failed");
    }
  };

  return (
    <div className="mx-auto max-w-6xl px-6 py-8">
      <Header
        title="New Analysis"
        description="Upload a resume, paste a job description, and start a private AI review."
      />
      {phase === "upload" && (
        <WorkflowPanel step="STEP 1" title="Upload Your Resume">
          <label className="flex min-h-64 cursor-pointer flex-col items-center justify-center rounded-lg border-2 border-dashed border-slate-200 bg-slate-50 text-center hover:border-violet-300">
            <Upload className="mb-4 h-10 w-10 text-violet-600" />
            <span className="font-semibold">
              {resume ? resume.name : "Drop your PDF here"}
            </span>
            <span className="mt-2 text-sm text-slate-500">
              PDF only, max 5MB
            </span>
            <input
              type="file"
              accept=".pdf"
              className="hidden"
              onChange={(event) => setResume(event.target.files?.[0] ?? null)}
            />
          </label>
          <div className="mt-6 flex justify-end">
            <Button disabled={!resume} onClick={() => setPhase("job")}>
              Continue
            </Button>
          </div>
        </WorkflowPanel>
      )}

      {phase === "job" && (
        <WorkflowPanel step="STEP 2" title="Paste Job Description">
          <div className="mb-4 grid gap-4 md:grid-cols-2">
            <label className="block">
              <span className="text-sm font-medium text-slate-700">
                Job Title
              </span>
              <input
                value={jobTitle}
                onChange={(event) => setJobTitle(event.target.value)}
                className="mt-2 h-10 w-full rounded-lg border border-slate-200 px-3 text-sm outline-none focus:border-violet-400 focus:ring-4 focus:ring-violet-100"
                placeholder="e.g. Data Analyst (Optional)"
              />
            </label>
            <label className="block">
              <span className="text-sm font-medium text-slate-700">
                Company Name
              </span>
              <input
                value={company}
                onChange={(event) => setCompany(event.target.value)}
                className="mt-2 h-10 w-full rounded-lg border border-slate-200 px-3 text-sm outline-none focus:border-violet-400 focus:ring-4 focus:ring-violet-100"
                placeholder="e.g. Acme Research (Optional)"
              />
            </label>
          </div>
          <textarea
            value={jdText}
            onChange={(event) => setJdText(event.target.value)}
            className="min-h-56 w-full rounded-lg border border-slate-200 p-4 text-sm outline-none focus:border-violet-400 focus:ring-4 focus:ring-violet-100"
            placeholder="Paste the full job description..."
          />
          {error && <p className="mt-3 text-sm text-red-600">{error}</p>}
          <div className="mt-6 flex justify-between">
            <Button variant="outline" onClick={() => setPhase("upload")}>
              Back
            </Button>
            <Button disabled={!resume || !jdText.trim()} onClick={start}>
              Start AI Analysis
              <ArrowRight className="h-4 w-4" />
            </Button>
          </div>
        </WorkflowPanel>
      )}

      {phase === "processing" && (
        <WorkflowPanel step="STEP 3" title="AI Analysis in Progress">
          <div className="grid gap-6 lg:grid-cols-[1fr_280px]">
            <div className="space-y-3">
              {workflowSteps
                .filter(({ step }) => !hiddenSteps.has(step))
                .map(({ step, label }) => {
                  const status = stepStatus[step] ?? "waiting";
                  return (
                    <div
                      key={label}
                      className="flex items-center justify-between rounded-lg border border-slate-200 p-4"
                    >
                      <div className="flex items-center gap-3">
                        {status === "done" ? (
                          <CheckCircle2 className="h-5 w-5 text-emerald-500" />
                        ) : status === "running" ? (
                          <Loader2 className="h-5 w-5 animate-spin text-violet-600" />
                        ) : (
                          <Clock3 className="h-5 w-5 text-slate-300" />
                        )}
                        <span className="font-medium">{label}</span>
                      </div>
                      <span className="text-xs text-slate-500">
                        {statusLabel(status)}
                      </span>
                    </div>
                  );
                })}
            </div>
            <Card className="p-6">
              <p className="text-sm font-semibold text-slate-600">
                Analysis Progress
              </p>
              <div className="mt-6 text-5xl font-bold">{progress}%</div>
              <Progress className="mt-5" value={progress} />
              <p className="mt-4 text-sm text-slate-500">
                {estimatedTimeLabel(progress, startedAt)}
              </p>
            </Card>
          </div>
        </WorkflowPanel>
      )}

      {phase === "results" && <ResultsPanel result={analysisResult} />}
    </div>
  );
}

function createInitialStepStatus(): Record<string, StepStatus> {
  return Object.fromEntries(
    workflowSteps.map(({ step }) => [step, "waiting"]),
  ) as Record<string, StepStatus>;
}

function createInitialHiddenSteps() {
  return new Set(supervisorBranchSteps);
}

function markUnfinishedStepsSkipped(current: Record<string, StepStatus>) {
  return Object.fromEntries(
    workflowSteps.map(({ step }) => [
      step,
      current[step] === "done" || current[step] === "running"
        ? "done"
        : "skipped",
    ]),
  ) as Record<string, StepStatus>;
}

function normalizeWorkflowStep(step?: string) {
  if (!step) return "";
  if (
    step === "extract_resume" ||
    step === "extract_resume_text" ||
    step === "queued"
  ) {
    return "parsing";
  }
  return step;
}

function updateStepStatuses(
  current: Record<string, StepStatus>,
  activeStep: string,
  activeStatus: StepStatus,
) {
  const next = { ...current };
  const activeIndex = workflowSteps.findIndex(
    ({ step }) => step === activeStep,
  );
  const bypassingAgents =
    activeStep === "rewrite" && current.supervisor === "waiting";

  if (bypassingAgents) {
    for (const step of skippedWhenAgentsBypassed) {
      next[step] = "skipped";
    }
  }

  if (activeIndex >= 0) {
    for (const { step } of workflowSteps.slice(0, activeIndex)) {
      if (next[step] === "waiting" || next[step] === "running") {
        next[step] = "done";
      }
    }
  }

  next[activeStep] = activeStatus;
  return next;
}

function markCompletedResultSteps(
  current: Record<string, StepStatus>,
  ranSteps: Set<string>,
) {
  const next = { ...current };
  for (const { step } of workflowSteps) {
    if (ranSteps.has(step) || next[step] === "running") {
      next[step] = "done";
    } else if (next[step] === "waiting") {
      next[step] = "skipped";
    }
  }
  return next;
}

function statusLabel(status: StepStatus) {
  if (status === "done") return "Done";
  if (status === "running") return "Running";
  if (status === "skipped") return "Skipped";
  return "Waiting";
}

function estimatedTimeLabel(progress: number, startedAt: number | null) {
  if (!startedAt || progress <= 5) return "Estimated time: Calculating...";
  if (progress >= 100) return "Estimated time: Complete";

  const elapsedSeconds = Math.max(1, (Date.now() - startedAt) / 1000);
  const remainingSeconds = Math.ceil(
    (elapsedSeconds / progress) * (100 - progress),
  );

  if (remainingSeconds < 60) {
    return `Estimated time: about ${remainingSeconds}s remaining`;
  }

  const minutes = Math.floor(remainingSeconds / 60);
  const seconds = remainingSeconds % 60;
  return `Estimated time: about ${minutes}m ${seconds}s remaining`;
}
