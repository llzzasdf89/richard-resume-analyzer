import {
  Crosshair,
  FileCheck2,
  FileText,
  Info,
  LineChart,
  Network,
  PencilLine,
  ShieldCheck,
} from "lucide-react";

import { workflowSteps } from "@/components/resume-analyzer/workflowSteps";
import { Card } from "@/components/ui/card";

const agentNodes = [
  {
    title: "Parser",
    description: "Extracts text and structure",
    icon: FileText,
    className: "mx-auto",
    tone: "bg-violet-100 text-violet-700",
  },
  {
    title: "JD Analyst",
    description: "Extracts requirements and priorities",
    icon: FileCheck2,
    className: "justify-self-start",
    tone: "bg-emerald-100 text-emerald-700",
  },
  {
    title: "Skill Graph",
    description: "Builds skills and experience graph",
    icon: Network,
    className: "justify-self-end",
    tone: "bg-blue-100 text-blue-700",
  },
  {
    title: "Matcher",
    description: "Matches profile to role and scores",
    icon: Crosshair,
    className: "mx-auto",
    tone: "bg-violet-100 text-violet-700",
  },
  {
    title: "ATS Check",
    description: "Validates ATS compatibility and readability",
    icon: ShieldCheck,
    className: "justify-self-start",
    tone: "bg-orange-100 text-orange-700",
  },
  {
    title: "Rewrite Agent",
    description: "Generates tailored, optimized resume",
    icon: PencilLine,
    className: "justify-self-end",
    tone: "bg-violet-100 text-violet-700",
  },
];

export function WorkflowPage() {
  return (
    <>
      <div className="mx-auto grid max-w-7xl items-center gap-12 px-6 py-16 lg:grid-cols-[0.85fr_1.15fr]">
        <div>
          <h1 className="max-w-2xl text-5xl font-bold leading-tight">
            From resume to role-fit signal
          </h1>
          <p className="mt-5 max-w-2xl text-lg leading-8 text-slate-300">
            See how the analysis moves through parsing, job requirements, skill
            matching, recommendations, and rewrite.
          </p>
        </div>

        <Card className="border-white/10 bg-white/[0.04] p-8 text-white shadow-2xl shadow-violet-950/40">
          <div className="grid grid-cols-5 items-start gap-3">
            {workflowSteps.map((step, index) => (
              <div key={step.title} className="relative text-center">
                {index < workflowSteps.length - 1 && (
                  <div className="absolute left-[calc(50%+2rem)] top-8 hidden h-px w-[calc(100%-4rem)] bg-slate-500 md:block" />
                )}
                <div
                  className={`mx-auto flex h-16 w-16 items-center justify-center rounded-full border ${
                    index === 0
                      ? "border-violet-500 text-violet-300 shadow-lg shadow-violet-700/30"
                      : "border-slate-600 text-slate-300"
                  }`}
                >
                  <step.icon className="h-6 w-6" />
                </div>
                <p className="mt-4 text-sm font-medium text-white">
                  {stageLabel(step.title)}
                </p>
              </div>
            ))}
          </div>
          <p className="mt-8 text-center text-sm text-slate-300">
            Five stages. One intelligent workflow. Better outcomes.
          </p>
        </Card>
      </div>

      <section className="bg-slate-50 text-slate-950">
        <div className="mx-auto grid max-w-7xl gap-6 px-6 py-8 lg:grid-cols-[1.35fr_1fr]">
          <Card className="p-6 flex justify-center">
            <div className="relative">
              <div className="absolute bottom-8 left-5 top-8 w-px bg-violet-500" />
              <div className="space-y-0">
                {workflowSteps.map((step, index) => (
                  <div
                    key={step.title}
                    className="relative grid grid-cols-[3rem_4rem_1fr_auto] items-center gap-4 border-b border-slate-200 py-5 last:border-b-0"
                  >
                    <div className="z-10 flex h-10 w-10 items-center justify-center rounded-full border border-slate-200 bg-white text-lg font-semibold text-violet-600">
                      {index + 1}
                    </div>
                    <div className="flex h-12 w-12 items-center justify-center rounded-lg bg-violet-100 text-violet-700">
                      <step.icon className="h-6 w-6" />
                    </div>
                    <div>
                      <h2 className="font-semibold">{step.title}</h2>
                      <p className="mt-1 text-sm text-slate-500">
                        {step.description}
                      </p>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          </Card>

          <Card className="p-6">
            <div className="mb-6 flex items-center gap-2">
              <h2 className="text-lg font-semibold">Multi-agent workflow</h2>
              <Info className="h-4 w-4 text-slate-400" />
            </div>
            <div className="relative min-h-[390px]">
              <ConnectorLines />
              <div className="relative grid grid-cols-2 gap-x-20 gap-y-8">
                <AgentNode node={agentNodes[0]} className="col-span-2" />
                <AgentNode node={agentNodes[1]} />
                <AgentNode node={agentNodes[2]} />
                <AgentNode node={agentNodes[3]} className="col-span-2" />
                <AgentNode node={agentNodes[4]} />
                <AgentNode node={agentNodes[5]} />
              </div>
            </div>
          </Card>
        </div>
      </section>

      <section className="bg-slate-50 text-slate-950">
        <div className="mx-auto flex max-w-7xl gap-6 px-6 pb-12 lg:grid-cols-[1fr_1fr_1fr_2.1fr]">
          <MetricCard
            icon={FileText}
            title="Inputs"
            value="2"
            label="Documents"
            detail="Resume + Job Description"
            tone="bg-violet-100 text-violet-700"
          />
          <MetricCard
            icon={LineChart}
            title="Signals"
            value="48+"
            label="Data Points"
            detail="Skills, Experience, Keywords, More"
            tone="bg-emerald-100 text-emerald-700"
          />
          <MetricCard
            icon={FileCheck2}
            title="Outputs"
            value="1"
            label="Optimized Resume"
            detail="Recommendations + Rewrite"
            tone="bg-blue-100 text-blue-700"
          />
        </div>
      </section>
    </>
  );
}

function AgentNode({
  node,
  className = "",
}: {
  node: (typeof agentNodes)[number];
  className?: string;
}) {
  return (
    <div
      className={`${node.className} ${className} z-10 w-48 rounded-lg border border-slate-200 bg-white p-3 shadow-sm`}
    >
      <div className="flex items-center gap-3">
        <div
          className={`flex h-10 w-10 items-center justify-center rounded-lg ${node.tone}`}
        >
          <node.icon className="h-5 w-5" />
        </div>
        <div>
          <p className="text-sm font-semibold">{node.title}</p>
          <p className="mt-1 text-xs leading-4 text-slate-500">
            {node.description}
          </p>
        </div>
      </div>
    </div>
  );
}

function ConnectorLines() {
  return (
    <div className="pointer-events-none absolute inset-0 hidden md:block">
      <div className="absolute left-1/2 top-[3.5rem] h-14 w-px bg-slate-300" />
      <div className="absolute left-[18%] right-[18%] top-[7rem] h-px bg-slate-300" />
      <div className="absolute left-[18%] top-[7rem] h-12 w-px bg-slate-300" />
      <div className="absolute right-[18%] top-[7rem] h-12 w-px bg-slate-300" />
      <div className="absolute left-[18%] right-[18%] top-[12rem] h-px bg-slate-300" />
      <div className="absolute left-1/2 top-[12rem] h-14 w-px bg-slate-300" />
      <div className="absolute left-1/2 top-[17.5rem] h-12 w-px bg-slate-300" />
      <div className="absolute left-[18%] right-[18%] top-[20.5rem] h-px bg-slate-300" />
      <div className="absolute left-[18%] top-[20.5rem] h-12 w-px bg-slate-300" />
      <div className="absolute right-[18%] top-[20.5rem] h-12 w-px bg-slate-300" />
    </div>
  );
}

function MetricCard({
  icon: Icon,
  title,
  value,
  label,
  detail,
  tone,
}: {
  icon: typeof FileText;
  title: string;
  value: string;
  label: string;
  detail: string;
  tone: string;
}) {
  return (
    <Card className="p-6 flex-1">
      <div
        className={`mb-4 flex h-12 w-12 items-center justify-center rounded-lg ${tone}`}
      >
        <Icon className="h-6 w-6" />
      </div>
      <h2 className="font-semibold">{title}</h2>
      <p className="mt-3 text-3xl font-bold">{value}</p>
      <p className="mt-1 text-sm text-slate-600">{label}</p>
      <p className="mt-4 text-xs text-slate-400">{detail}</p>
    </Card>
  );
}

function stageLabel(title: string) {
  if (title === "Upload resume") return "Upload";
  if (title === "Read job description") return "Job description";
  if (title === "Build match profile") return "Match profile";
  if (title === "Generate recommendations") return "Recommendations";
  return "Rewrite";
}
