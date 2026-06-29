import { useMemo, useState } from "react";
import {
  ArrowRight,
  CheckCircle2,
  Clock3,
  Loader2,
  Upload,
} from "lucide-react";

import { createAnalysis } from "@/api/analyses";
import { Header } from "@/components/resume-analyzer/Header";
import { ResultsPanel } from "@/components/resume-analyzer/ResultsPanel";
import { WorkflowPanel } from "@/components/resume-analyzer/WorkflowPanel";
import { Button } from "@/components/ui/button";
import { Card } from "@/components/ui/card";
import { Progress } from "@/components/ui/progress";
import { createRequestId } from "@/lib/requestId";

type AnalysisPhase = "upload" | "job" | "processing" | "results";

const workflowSteps = [
  "Parsing Resume",
  "Understanding Job Description",
  "Building Skill Graph",
  "Comparing Experience",
  "ATS Evaluation",
  "Resume Rewrite",
  "Career Advisor",
];

export function NewAnalysisPage() {
  const [phase, setPhase] = useState<AnalysisPhase>("upload");
  const [resume, setResume] = useState<File | null>(null);
  const [jdText, setJdText] = useState("");
  const [progress, setProgress] = useState(0);
  const [error, setError] = useState("");

  const activeStep = useMemo(
    () => Math.min(workflowSteps.length - 1, Math.floor(progress / 16)),
    [progress],
  );

  const start = async () => {
    if (!resume || !jdText.trim()) return;
    setError("");
    setPhase("processing");
    setProgress(12);
    try {
      await createAnalysis({ resume, jdText }, createRequestId());
      const timer = window.setInterval(() => {
        setProgress((value) => {
          const next = Math.min(100, value + 14);
          if (next === 100) {
            window.clearInterval(timer);
            setPhase("results");
          }
          return next;
        });
      }, 500);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Analysis failed");
      setPhase("job");
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
            <span className="font-semibold">{resume ? resume.name : "Drop your PDF here"}</span>
            <span className="mt-2 text-sm text-slate-500">PDF only, max 5MB</span>
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
              {workflowSteps.map((label, index) => (
                <div
                  key={label}
                  className="flex items-center justify-between rounded-lg border border-slate-200 p-4"
                >
                  <div className="flex items-center gap-3">
                    {index < activeStep ? (
                      <CheckCircle2 className="h-5 w-5 text-emerald-500" />
                    ) : index === activeStep ? (
                      <Loader2 className="h-5 w-5 animate-spin text-violet-600" />
                    ) : (
                      <Clock3 className="h-5 w-5 text-slate-300" />
                    )}
                    <span className="font-medium">{label}</span>
                  </div>
                  <span className="text-xs text-slate-500">
                    {index < activeStep ? "Done" : index === activeStep ? "Running" : "Waiting"}
                  </span>
                </div>
              ))}
            </div>
            <Card className="p-6">
              <p className="text-sm font-semibold text-slate-600">Analysis Progress</p>
              <div className="mt-6 text-5xl font-bold">{progress}%</div>
              <Progress className="mt-5" value={progress} />
              <p className="mt-4 text-sm text-slate-500">Estimated time: 30-60 seconds</p>
            </Card>
          </div>
        </WorkflowPanel>
      )}

      {phase === "results" && <ResultsPanel />}
    </div>
  );
}
