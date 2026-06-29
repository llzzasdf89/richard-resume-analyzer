import {
  ArrowRight,
  BarChart3,
  FileText,
  Sparkles,
  Upload,
} from "lucide-react";
import { useNavigate } from "react-router-dom";

import { ScoreLine } from "@/components/resume-analyzer/ScoreLine";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card } from "@/components/ui/card";

export function LandingPage() {
  const navigate = useNavigate();
  const onGetStarted = () => navigate("/login");

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
        <Button onClick={onGetStarted} className="cursor-pointer">
          Get Started
        </Button>
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
            Upload your resume, paste a target job description, and receive a
            private analysis report with match score, gaps, strengths, and
            rewrite suggestions.
          </p>
          <div className="mt-8 flex flex-wrap gap-4">
            <Button onClick={onGetStarted} className="h-12 px-6 cursor-pointer">
              Analyze My Resume
              <ArrowRight className="h-4 w-4" />
            </Button>
            <Button
              variant="outline"
              className="h-12 border-white/20 bg-transparent px-6 text-white hover:bg-white/10 cursor-pointer"
            >
              See Workflow
            </Button>
          </div>
        </div>

        <div className="relative">
          <div className="absolute inset-0 rounded-full bg-violet-600/20 blur-3xl" />
          <Card className="relative mx-auto max-w-md border-cyan-400/20 bg-slate-950/90 p-6 text-white shadow-2xl shadow-violet-900/40">
            <div className="mb-6 flex items-center justify-between">
              <span className="text-sm text-slate-400">
                Overall Match Score
              </span>
              <Badge className="border-emerald-400/30 bg-emerald-400/10 text-emerald-200">
                Live Preview
              </Badge>
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
            [
              "Paste Job Description",
              FileText,
              "Add the target role description.",
            ],
            [
              "AI Analysis",
              Sparkles,
              "Specialist agents evaluate fit and gaps.",
            ],
            [
              "Get Actionable Insights",
              BarChart3,
              "Download a private PDF report.",
            ],
          ].map(([title, Icon, description]) => (
            <Card key={title as string} className="p-6">
              <div className="mb-5 flex h-12 w-12 items-center justify-center rounded-lg bg-violet-100 text-violet-700">
                <Icon className="h-5 w-5" />
              </div>
              <h3 className="font-semibold">{title as string}</h3>
              <p className="mt-2 text-sm leading-6 text-slate-500">
                {description as string}
              </p>
            </Card>
          ))}
        </div>
      </section>
    </main>
  );
}
