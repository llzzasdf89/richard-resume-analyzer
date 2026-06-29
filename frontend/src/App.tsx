import { useEffect, useMemo, useState } from "react";
import type { Session } from "@supabase/supabase-js";
import {
  ArrowRight,
  BarChart3,
  CheckCircle2,
  Code2,
  Clock3,
  FileText,
  History,
  LayoutDashboard,
  Loader2,
  Lock,
  LogOut,
  Sparkles,
  Upload,
} from "lucide-react";
import { createAnalysis, listAnalyses, type AnalysisListItem } from "./api/analyses";
import { createRequestId } from "./lib/requestId";
import { isSupabaseConfigured, supabase, supabaseConfigMessage } from "./lib/supabase";
import { Badge } from "./components/ui/badge";
import { Button } from "./components/ui/button";
import { Card } from "./components/ui/card";
import { Progress } from "./components/ui/progress";

type View = "landing" | "login" | "new-analysis" | "history" | "resumes";
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

export default function App() {
  const [session, setSession] = useState<Session | null>(null);
  const [view, setView] = useState<View>("landing");

  useEffect(() => {
    if (!isSupabaseConfigured) return;

    supabase.auth.getSession().then(({ data }) => {
      setSession(data.session);
      if (data.session) setView("new-analysis");
    });
    const { data } = supabase.auth.onAuthStateChange((_event, nextSession) => {
      setSession(nextSession);
      setView(nextSession ? "new-analysis" : "landing");
    });
    return () => data.subscription.unsubscribe();
  }, []);

  if (!session && view === "login") {
    return <LoginPage onBack={() => setView("landing")} />;
  }

  if (!session) {
    return <LandingPage onGetStarted={() => setView("login")} />;
  }

  return (
    <AppShell session={session} view={view} onViewChange={setView}>
      {view === "new-analysis" && <NewAnalysisPage />}
      {view === "history" && <HistoryPage />}
      {view === "resumes" && <SavedResumesPage />}
    </AppShell>
  );
}

function LandingPage({ onGetStarted }: { onGetStarted: () => void }) {
  return (
    <main className="min-h-screen bg-[#060a12] text-white">
      <header className="mx-auto flex max-w-7xl items-center justify-between px-6 py-6">
        <div className="flex items-center gap-3">
          <div className="flex h-9 w-9 items-center justify-center rounded-full bg-violet-600">
            <Sparkles className="h-4 w-4" />
          </div>
          <span className="font-semibold">Resume Analyzer</span>
        </div>
        <nav className="hidden items-center gap-8 text-sm text-slate-300 md:flex">
          <a href="#features">Features</a>
          <a href="#workflow">How It Works</a>
          <a href="#about">About</a>
        </nav>
        <Button onClick={onGetStarted}>Get Started</Button>
      </header>

      <section className="mx-auto grid max-w-7xl items-center gap-12 px-6 pb-20 pt-14 lg:grid-cols-[1.05fr_0.95fr]">
        <div>
          <Badge className="border-violet-500/30 bg-white/5 text-violet-100">
            AI Powered · Multi-Agent System
          </Badge>
          <h1 className="mt-6 max-w-3xl text-5xl font-bold leading-tight tracking-normal md:text-7xl">
            AI Resume Analyzer
            <span className="block bg-gradient-to-r from-sky-400 to-violet-500 bg-clip-text text-transparent">
              Get Hired Faster
            </span>
          </h1>
          <p className="mt-6 max-w-2xl text-base leading-7 text-slate-300">
            Upload your resume, paste a target job description, and receive a private analysis report with match score, gaps, strengths, and rewrite suggestions.
          </p>
          <div className="mt-8 flex flex-wrap gap-4">
            <Button onClick={onGetStarted} className="h-12 px-6">
              Analyze My Resume
              <ArrowRight className="h-4 w-4" />
            </Button>
            <Button variant="outline" className="h-12 border-white/20 bg-transparent px-6 text-white hover:bg-white/10">
              See Workflow
            </Button>
          </div>
        </div>

        <div className="relative">
          <div className="absolute inset-0 rounded-full bg-violet-600/20 blur-3xl" />
          <Card className="relative mx-auto max-w-md border-cyan-400/20 bg-slate-950/90 p-6 text-white shadow-2xl shadow-violet-900/40">
            <div className="mb-6 flex items-center justify-between">
              <span className="text-sm text-slate-400">Overall Match Score</span>
              <Badge className="border-emerald-400/30 bg-emerald-400/10 text-emerald-200">Live Preview</Badge>
            </div>
            <div className="mx-auto flex h-36 w-36 items-center justify-center rounded-full border-[10px] border-violet-500">
              <div className="text-center">
                <div className="text-4xl font-bold">87%</div>
                <div className="text-xs text-emerald-300">Excellent Match</div>
              </div>
            </div>
            <div className="mt-8 space-y-4">
              <ScoreLine label="Skills Match" value={92} />
              <ScoreLine label="Experience Match" value={85} />
              <ScoreLine label="Education Match" value={78} />
              <ScoreLine label="ATS Score" value={90} />
            </div>
          </Card>
        </div>
      </section>

      <section id="workflow" className="bg-slate-50 px-6 py-16 text-slate-950">
        <h2 className="text-center text-3xl font-bold">How It Works</h2>
        <div className="mx-auto mt-10 grid max-w-6xl gap-5 md:grid-cols-4">
          {[
            ["Upload Resume", Upload, "Upload a PDF resume up to 5MB."],
            ["Paste Job Description", FileText, "Add the target role description."],
            ["AI Analysis", Sparkles, "Specialist agents evaluate fit and gaps."],
            ["Get Actionable Insights", BarChart3, "Download a private PDF report."],
          ].map(([title, Icon, description]) => (
            <Card key={title as string} className="p-6">
              <div className="mb-5 flex h-12 w-12 items-center justify-center rounded-lg bg-violet-100 text-violet-700">
                <Icon className="h-5 w-5" />
              </div>
              <h3 className="font-semibold">{title as string}</h3>
              <p className="mt-2 text-sm leading-6 text-slate-500">{description as string}</p>
            </Card>
          ))}
        </div>
      </section>
    </main>
  );
}

function LoginPage({ onBack }: { onBack: () => void }) {
  const [authError, setAuthError] = useState("");

  const signIn = async (provider: "google" | "github") => {
    if (!isSupabaseConfigured) {
      setAuthError(supabaseConfigMessage);
      return;
    }

    const { error } = await supabase.auth.signInWithOAuth({
      provider,
      options: {
        redirectTo: window.location.origin,
      },
    });

    if (error) setAuthError(error.message);
  };

  return (
    <main className="grid min-h-screen bg-slate-50 lg:grid-cols-[1.1fr_0.9fr]">
      <section className="flex items-center bg-[#060a12] px-8 py-12 text-white">
        <div className="mx-auto max-w-xl">
          <Badge className="border-violet-500/30 bg-white/5 text-violet-100">
            Private Resume Workspace
          </Badge>
          <h1 className="mt-6 text-5xl font-bold leading-tight">Keep every resume analysis in one secure place.</h1>
          <p className="mt-5 text-slate-300">
            Sign in to keep your resume files, job descriptions, reports, and analysis history tied to your private account.
          </p>
        </div>
      </section>
      <section className="flex items-center justify-center px-6">
        <Card className="w-full max-w-md p-8">
          <button onClick={onBack} className="mb-8 text-sm text-slate-500 hover:text-slate-900">
            Back to home
          </button>
          <h2 className="text-2xl font-bold text-slate-950">Sign in</h2>
          <p className="mt-2 text-sm text-slate-500">Use the provider that matches your developer workflow.</p>
          {!isSupabaseConfigured && (
            <div className="mt-6 rounded-lg border border-amber-200 bg-amber-50 px-4 py-3 text-sm leading-6 text-amber-900">
              {supabaseConfigMessage}
            </div>
          )}
          {authError && (
            <div className="mt-6 rounded-lg border border-rose-200 bg-rose-50 px-4 py-3 text-sm leading-6 text-rose-900">
              {authError}
            </div>
          )}
          <div className="mt-8 space-y-3">
            <Button variant="outline" className="w-full justify-start" disabled={!isSupabaseConfigured} onClick={() => signIn("google")}>
              <Lock className="h-4 w-4" />
              Continue with Google
            </Button>
            <Button variant="secondary" className="w-full justify-start" disabled={!isSupabaseConfigured} onClick={() => signIn("github")}>
              <Code2 className="h-4 w-4" />
              Continue with GitHub
            </Button>
          </div>
        </Card>
      </section>
    </main>
  );
}

function AppShell({
  children,
  session,
  view,
  onViewChange,
}: {
  children: React.ReactNode;
  session: Session;
  view: View;
  onViewChange: (view: View) => void;
}) {
  const user = session.user;
  const navItems = [
    ["new-analysis", LayoutDashboard, "New Analysis"],
    ["history", History, "History"],
    ["resumes", FileText, "Saved Resumes"],
  ] as const;

  return (
    <main className="min-h-screen bg-slate-50 text-slate-950">
      <aside className="fixed inset-y-0 left-0 hidden w-64 border-r border-slate-200 bg-white p-5 md:flex md:flex-col">
        <div className="mb-8 flex items-center gap-3">
          <div className="flex h-9 w-9 items-center justify-center rounded-full bg-violet-600 text-white">
            <Sparkles className="h-4 w-4" />
          </div>
          <span className="font-semibold">Resume Analyzer</span>
        </div>
        <nav className="space-y-2">
          {navItems.map(([key, Icon, label]) => (
            <button
              key={key}
              onClick={() => onViewChange(key)}
              className={`flex w-full items-center gap-3 rounded-lg px-3 py-2 text-sm font-medium transition ${
                view === key ? "bg-violet-100 text-violet-700" : "text-slate-600 hover:bg-slate-100"
              }`}
            >
              <Icon className="h-4 w-4" />
              {label}
            </button>
          ))}
        </nav>
        <div className="mt-auto rounded-lg border border-slate-200 p-3">
          <p className="truncate text-sm font-semibold">{user.email}</p>
          <button
            className="mt-3 flex items-center gap-2 text-sm text-slate-500 hover:text-slate-950"
            onClick={() => supabase.auth.signOut()}
          >
            <LogOut className="h-4 w-4" />
            Sign out
          </button>
        </div>
      </aside>
      <section className="md:pl-64">{children}</section>
    </main>
  );
}

function NewAnalysisPage() {
  const [phase, setPhase] = useState<AnalysisPhase>("upload");
  const [resume, setResume] = useState<File | null>(null);
  const [jdText, setJdText] = useState("");
  const [progress, setProgress] = useState(0);
  const [error, setError] = useState("");

  const activeStep = useMemo(() => Math.min(workflowSteps.length - 1, Math.floor(progress / 16)), [progress]);

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
      <Header title="New Analysis" description="Upload a resume, paste a job description, and start a private AI review." />
      {phase === "upload" && (
        <WorkflowPanel step="STEP 1" title="Upload Your Resume">
          <label className="flex min-h-64 cursor-pointer flex-col items-center justify-center rounded-lg border-2 border-dashed border-slate-200 bg-slate-50 text-center hover:border-violet-300">
            <Upload className="mb-4 h-10 w-10 text-violet-600" />
            <span className="font-semibold">{resume ? resume.name : "Drop your PDF here"}</span>
            <span className="mt-2 text-sm text-slate-500">PDF only, max 5MB</span>
            <input type="file" accept=".pdf" className="hidden" onChange={(event) => setResume(event.target.files?.[0] ?? null)} />
          </label>
          <div className="mt-6 flex justify-end">
            <Button disabled={!resume} onClick={() => setPhase("job")}>Continue</Button>
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
            <Button variant="outline" onClick={() => setPhase("upload")}>Back</Button>
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
                <div key={label} className="flex items-center justify-between rounded-lg border border-slate-200 p-4">
                  <div className="flex items-center gap-3">
                    {index < activeStep ? <CheckCircle2 className="h-5 w-5 text-emerald-500" /> : index === activeStep ? <Loader2 className="h-5 w-5 animate-spin text-violet-600" /> : <Clock3 className="h-5 w-5 text-slate-300" />}
                    <span className="font-medium">{label}</span>
                  </div>
                  <span className="text-xs text-slate-500">{index < activeStep ? "Done" : index === activeStep ? "Running" : "Waiting"}</span>
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

function ResultsPanel() {
  return (
    <WorkflowPanel step="STEP 4" title="Analysis Results">
      <div className="grid gap-6 lg:grid-cols-2">
        <Card className="p-6 text-center">
          <p className="font-semibold">Overall Match Score</p>
          <div className="mx-auto mt-6 flex h-36 w-36 items-center justify-center rounded-full border-[10px] border-violet-600">
            <div>
              <div className="text-4xl font-bold">87%</div>
              <div className="text-sm text-emerald-600">Excellent Match</div>
            </div>
          </div>
        </Card>
        <Card className="p-6">
          <p className="font-semibold">Score Breakdown</p>
          <div className="mt-6 space-y-4">
            <ScoreLine label="Skills Match" value={92} />
            <ScoreLine label="Experience Match" value={85} />
            <ScoreLine label="Education Match" value={78} />
            <ScoreLine label="ATS Score" value={90} />
          </div>
        </Card>
      </div>
      <div className="mt-6 grid gap-4 md:grid-cols-3">
        <InsightCard title="Top Strengths" items={["Strong Python and FastAPI skills", "Good database experience", "Cloud platform exposure"]} />
        <InsightCard title="Key Gaps" items={["System design depth", "AI/ML production examples", "Leadership examples"]} />
        <InsightCard title="Recommendations" items={["Add project metrics", "Highlight AI projects", "Include ownership examples"]} />
      </div>
    </WorkflowPanel>
  );
}

function HistoryPage() {
  const [items, setItems] = useState<AnalysisListItem[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState("");

  useEffect(() => {
    let isMounted = true;

    listAnalyses()
      .then((nextItems) => {
        if (isMounted) setItems(nextItems);
      })
      .catch((err) => {
        if (isMounted) setError(err instanceof Error ? err.message : "Failed to load history");
      })
      .finally(() => {
        if (isMounted) setIsLoading(false);
      });

    return () => {
      isMounted = false;
    };
  }, []);

  return (
    <div className="mx-auto max-w-6xl px-6 py-8">
      <Header title="History" description="Review previous resume analyses and reports." />
      <Card className="p-6">
        {isLoading && <EmptyState title="Loading history" description="Fetching your previous analysis records." />}
        {!isLoading && error && <EmptyState title="Unable to load history" description={error} />}
        {!isLoading && !error && items.length === 0 && (
          <EmptyState title="No analysis history yet" description="Run your first resume analysis to see it here." />
        )}
        {!isLoading && !error && items.length > 0 && (
          <div className="divide-y divide-slate-100">
            {items.map((item) => (
              <div key={item.id} className="flex flex-col gap-4 py-5 md:flex-row md:items-center md:justify-between">
                <div>
                  <div className="flex flex-wrap items-center gap-3">
                    <h2 className="font-semibold">{item.job_title || "Untitled role"}</h2>
                    <Badge className={statusBadgeClass(item.status)}>{item.status}</Badge>
                  </div>
                  <p className="mt-1 text-sm text-slate-500">
                    {item.company || "No company"} · {formatDate(item.created_at)}
                  </p>
                  <p className="mt-2 text-xs text-slate-400">Analysis ID: {item.id}</p>
                </div>
                <div className="flex items-center gap-6">
                  <div className="text-right">
                    <p className="text-sm text-slate-500">Score</p>
                    <p className="text-2xl font-bold">{item.score ?? "--"}{item.score !== null ? "%" : ""}</p>
                  </div>
                  <div className="w-36">
                    <Progress value={item.progress} />
                    <p className="mt-2 text-xs text-slate-500">{item.current_step || "waiting"}</p>
                  </div>
                </div>
              </div>
            ))}
          </div>
        )}
      </Card>
    </div>
  );
}

function SavedResumesPage() {
  return (
    <div className="mx-auto max-w-6xl px-6 py-8">
      <Header title="Saved Resumes" description="Manage original PDF files connected to your analysis reports." />
      <Card className="p-6">
        <EmptyState title="No saved resumes yet" description="Uploaded PDF resumes will appear here." />
      </Card>
    </div>
  );
}

function WorkflowPanel({ step, title, children }: { step: string; title: string; children: React.ReactNode }) {
  return (
    <section>
      <div className="mb-4 flex items-center gap-3">
        <Badge className="bg-violet-600 text-white">{step}</Badge>
        <h2 className="text-lg font-bold">{title}</h2>
      </div>
      <Card className="p-8">{children}</Card>
    </section>
  );
}

function Header({ title, description }: { title: string; description: string }) {
  return (
    <div className="mb-8">
      <h1 className="text-3xl font-bold">{title}</h1>
      <p className="mt-2 text-sm text-slate-500">{description}</p>
    </div>
  );
}

function ScoreLine({ label, value }: { label: string; value: number }) {
  return (
    <div>
      <div className="mb-2 flex justify-between text-sm">
        <span>{label}</span>
        <span className="font-semibold">{value}%</span>
      </div>
      <Progress value={value} />
    </div>
  );
}

function InsightCard({ title, items }: { title: string; items: string[] }) {
  return (
    <Card className="p-5">
      <h3 className="font-semibold">{title}</h3>
      <ul className="mt-4 space-y-3 text-sm text-slate-600">
        {items.map((item) => (
          <li key={item} className="flex gap-2">
            <CheckCircle2 className="mt-0.5 h-4 w-4 text-emerald-500" />
            <span>{item}</span>
          </li>
        ))}
      </ul>
    </Card>
  );
}

function EmptyState({ title, description }: { title: string; description: string }) {
  return (
    <div className="py-20 text-center">
      <FileText className="mx-auto h-10 w-10 text-slate-300" />
      <h2 className="mt-4 font-semibold">{title}</h2>
      <p className="mt-2 text-sm text-slate-500">{description}</p>
    </div>
  );
}

function statusBadgeClass(status: string) {
  if (status === "completed") return "border-emerald-200 bg-emerald-50 text-emerald-700";
  if (status === "failed") return "border-rose-200 bg-rose-50 text-rose-700";
  if (status === "processing") return "border-violet-200 bg-violet-50 text-violet-700";
  return "border-slate-200 bg-slate-50 text-slate-600";
}

function formatDate(value: string) {
  return new Intl.DateTimeFormat(undefined, {
    dateStyle: "medium",
    timeStyle: "short",
  }).format(new Date(value));
}
