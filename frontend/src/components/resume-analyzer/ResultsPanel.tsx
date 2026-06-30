import { InsightCard } from "@/components/resume-analyzer/InsightCard";
import { ScoreLine } from "@/components/resume-analyzer/ScoreLine";
import { WorkflowPanel } from "@/components/resume-analyzer/WorkflowPanel";
import { Card } from "@/components/ui/card";

export function ResultsPanel() {
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
        <InsightCard
          title="Top Strengths"
          items={[
            "Strong Python and FastAPI skills",
            "Good database experience",
            "Cloud platform exposure",
          ]}
        />
        <InsightCard
          title="Key Gaps"
          items={[
            "System design depth",
            "AI/ML production examples",
            "Leadership examples",
          ]}
        />
        <InsightCard
          title="Recommendations"
          items={[
            "Add project metrics",
            "Highlight AI projects",
            "Include ownership examples",
          ]}
        />
      </div>
    </WorkflowPanel>
  );
}
