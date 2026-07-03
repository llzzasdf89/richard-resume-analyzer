import type { AnalysisResult } from "@/api/analyses";
import { InsightCard } from "@/components/resume-analyzer/InsightCard";
import { ScoreLine } from "@/components/resume-analyzer/ScoreLine";
import { WorkflowPanel } from "@/components/resume-analyzer/WorkflowPanel";
import { Card } from "@/components/ui/card";

export function ResultsPanel({ result }: { result?: AnalysisResult | null }) {
  const score = result?.score ?? 0;
  const matchedCount = result?.matched_skills?.length ?? 0;
  const missingCount = result?.missing_skills?.length ?? 0;
  const totalSkillSignals = matchedCount + missingCount;
  const skillCoverage =
    totalSkillSignals > 0
      ? Math.round((matchedCount / totalSkillSignals) * 100)
      : score;
  const gapPressure =
    totalSkillSignals > 0
      ? Math.round((missingCount / totalSkillSignals) * 100)
      : 0;
  const matchedSkills = result?.matched_skills?.length
    ? result.matched_skills
    : [];
  const missingSkills = result?.missing_skills?.length
    ? result.missing_skills
    : ["No critical gaps detected"];
  const recommendations =
    result?.suggestions?.trim() ||
    "No specialist recommendations were returned for this analysis.";

  return (
    <WorkflowPanel step="STEP 4" title="Analysis Results">
      <div className="grid gap-6 lg:grid-cols-2">
        <Card className="p-6 text-center">
          <p className="font-semibold">Overall Match Score</p>
          <div className="mx-auto mt-6 flex h-36 w-36 items-center justify-center rounded-full border-[10px] border-violet-600">
            <div>
              <div className="text-4xl font-bold">{score}%</div>
              <div className="text-sm text-emerald-600">
                {scoreLabel(score)}
              </div>
            </div>
          </div>
        </Card>
        <Card className="p-6">
          <p className="font-semibold">Analysis Signals</p>
          <div className="mt-6 space-y-4">
            <ScoreLine label="Overall Match" value={score} />
            <ScoreLine label="Skill Coverage" value={skillCoverage} />
            <ScoreLine label="Gap Pressure" value={gapPressure} />
          </div>
        </Card>
      </div>
      <div className="mt-6 grid gap-4 md:grid-cols-2">
        <InsightCard title="Matched Skills" items={matchedSkills.slice(0, 3)} />
        <InsightCard
          title="Missing Skills"
          items={missingSkills.slice(0, 3)}
          tone="gap"
        />
      </div>
      <Card className="mt-6 p-6">
        <h3 className="font-semibold">Recommendations</h3>
        <div className="mt-4 max-h-[420px] overflow-auto rounded-lg border border-slate-200 bg-slate-50 p-4">
          <pre className="whitespace-pre-wrap break-words font-sans text-sm leading-6 text-slate-700">
            {recommendations}
          </pre>
        </div>
      </Card>
      <Card className="mt-6 p-6">
        <h3 className="font-semibold">Rewrite Reference</h3>
        <div className="mt-4 max-h-[420px] overflow-auto rounded-lg border border-slate-200 bg-slate-50 p-4">
          <pre className="whitespace-pre-wrap break-words font-sans text-sm leading-6 text-slate-700">
            {result?.rewritten_resume?.trim() ||
              "No rewrite reference was returned for this analysis."}
          </pre>
        </div>
      </Card>
    </WorkflowPanel>
  );
}

function scoreLabel(score: number) {
  if (score >= 90) return "Excellent Match";
  if (score >= 75) return "Strong Match";
  if (score >= 50) return "Partial Match";
  return "Low Match";
}
