import type { MatchResult } from "../types";
import SkillTags from "./SkillTags";

interface MatchScoreProps {
  result: MatchResult;
}

function ScoreRing({ score }: { score: number }) {
  const color = score >= 80 ? "#22c55e" : score >= 60 ? "#f59e0b" : "#ef4444";

  const radius = 40;
  const circumference = 2 * Math.PI * radius;
  const offset = circumference - (score / 100) * circumference;

  return (
    <div className="relative w-28 h-28 flex items-center justify-center">
      <svg className="absolute inset-0 -rotate-90" width="112" height="112">
        <circle
          cx="56"
          cy="56"
          r={radius}
          fill="none"
          stroke="#e5e7eb"
          strokeWidth="8"
        />
        <circle
          cx="56"
          cy="56"
          r={radius}
          fill="none"
          stroke={color}
          strokeWidth="8"
          strokeDasharray={circumference}
          strokeDashoffset={offset}
          strokeLinecap="round"
          style={{ transition: "stroke-dashoffset 0.8s ease" }}
        />
      </svg>
      <div className="text-center">
        <div className="text-2xl font-bold" style={{ color }}>
          {score}
        </div>
        <div className="text-xs text-gray-400">/ 100</div>
      </div>
    </div>
  );
}

export default function MatchScore({ result }: MatchScoreProps) {
  return (
    <div className="bg-white border border-gray-200 rounded-xl p-6 space-y-4">
      <div className="flex items-center gap-6">
        <ScoreRing score={result.score} />
        <div>
          <h3 className="font-semibold text-gray-800 mb-1">匹配度评分</h3>
          <p className="text-sm text-gray-500">
            {result.score >= 80
              ? "非常匹配，建议直接投递"
              : result.score >= 60
                ? "基本匹配，优化后投递"
                : "匹配度较低，建议针对性提升"}
          </p>
        </div>
      </div>

      {result.matched.length > 0 && (
        <div>
          <p className="text-xs font-medium text-gray-500 mb-2">
            ✅ 已匹配技能
          </p>
          <SkillTags skills={result.matched} variant="matched" />
        </div>
      )}

      {result.missing.length > 0 && (
        <div>
          <p className="text-xs font-medium text-gray-500 mb-2">❌ 缺失技能</p>
          <SkillTags skills={result.missing} variant="missing" />
        </div>
      )}
    </div>
  );
}
