import type { AnalysisState } from "../types";
import MatchScore from "./MatchScore";
import SkillTags from "./SkillTags";
interface AnalysisResultProps {
  state: AnalysisState;
}

export default function AnalysisResult({ state }: AnalysisResultProps) {
  if (state.status === "idle") return null;

  return (
    <div className="space-y-5">
      {/* JD 分析 */}
      {state.jdAnalysis && (
        <div className="bg-white border border-gray-200 rounded-xl p-6 space-y-3">
          <h3 className="font-semibold text-gray-800">📋 JD 分析</h3>
          <p className="text-sm text-gray-600">
            {state.jdAnalysis.requirements}
          </p>
          {state.jdAnalysis.must_skills.length > 0 && (
            <div>
              <p className="text-xs font-medium text-gray-500 mb-2">必备技能</p>
              <SkillTags
                skills={state.jdAnalysis.must_skills}
                variant="matched"
              />
            </div>
          )}
          {state.jdAnalysis.nice_skills.length > 0 && (
            <div>
              <p className="text-xs font-medium text-gray-500 mb-2">加分技能</p>
              <SkillTags skills={state.jdAnalysis.nice_skills} variant="nice" />
            </div>
          )}
        </div>
      )}

      {/* 匹配度 */}
      {state.matchResult && <MatchScore result={state.matchResult} />}

      {/* 优化建议 */}
      {state.suggestions && (
        <div className="bg-white border border-gray-200 rounded-xl p-6">
          <h3 className="font-semibold text-gray-800 mb-3">💡 优化建议</h3>
          <div className="text-sm text-gray-600 whitespace-pre-wrap leading-relaxed">
            {state.suggestions}
          </div>
        </div>
      )}

      {/* 重写简历 */}
      {state.rewrittenResume && (
        <div className="bg-white border border-gray-200 rounded-xl p-6">
          <div className="flex items-center justify-between mb-3">
            <h3 className="font-semibold text-gray-800">✍️ 优化后的简历</h3>
            <button
              onClick={() =>
                navigator.clipboard.writeText(state.rewrittenResume)
              }
              className="text-xs text-blue-600 hover:text-blue-700 font-medium"
            >
              复制
            </button>
          </div>
          <div
            className="text-sm text-gray-600 whitespace-pre-wrap leading-relaxed
            bg-gray-50 rounded-lg p-4 max-h-96 overflow-y-auto"
          >
            {state.rewrittenResume}
          </div>
        </div>
      )}

      {/* 加载中状态 */}
      {state.status === "loading" && !state.rewrittenResume && (
        <div className="flex items-center gap-3 text-sm text-gray-500 p-4">
          <div className="w-4 h-4 border-2 border-blue-500 border-t-transparent rounded-full animate-spin" />
          {state.currentStep?.message ?? "加载中"}
        </div>
      )}

      {/* 错误 */}
      {state.error && (
        <div className="bg-red-50 border border-red-200 rounded-xl p-4 text-sm text-red-600">
          ⚠️ {state.error}
        </div>
      )}
    </div>
  );
}
