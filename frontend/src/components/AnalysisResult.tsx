import type { AnalysisState } from "../types";
import MatchScore from "./MatchScore";
import SkillTags from "./SkillTags";
interface AnalysisResultProps {
  state: AnalysisState;
}

export default function AnalysisResult({ state }: AnalysisResultProps) {
  if (state.status === "idle") return null;

  const loadingMessage =
    "message" in state.currentStep ? state.currentStep.message : "Loading";

  return (
    <div className="space-y-5">
      {/* Job description analysis */}
      {state.jdAnalysis && (
        <div className="bg-white border border-gray-200 rounded-xl p-6 space-y-3">
          <h3 className="font-semibold text-gray-800">📋 Job Description Analysis</h3>
          <p className="text-sm text-gray-600">
            {state.jdAnalysis.requirements}
          </p>
          {state.jdAnalysis.must_skills.length > 0 && (
            <div>
              <p className="text-xs font-medium text-gray-500 mb-2">Required Skills</p>
              <SkillTags
                skills={state.jdAnalysis.must_skills}
                variant="matched"
              />
            </div>
          )}
          {state.jdAnalysis.nice_skills.length > 0 && (
            <div>
              <p className="text-xs font-medium text-gray-500 mb-2">Nice-to-Have Skills</p>
              <SkillTags skills={state.jdAnalysis.nice_skills} variant="nice" />
            </div>
          )}
        </div>
      )}

      {/* Match score */}
      {state.matchResult && <MatchScore result={state.matchResult} />}

      {/* Optimization suggestions */}
      {state.suggestions && (
        <div className="bg-white border border-gray-200 rounded-xl p-6">
          <h3 className="font-semibold text-gray-800 mb-3">💡 Optimization Suggestions</h3>
          <div className="text-sm text-gray-600 whitespace-pre-wrap leading-relaxed">
            {state.suggestions}
          </div>
        </div>
      )}

      {/* Rewritten resume */}
      {state.rewrittenResume && (
        <div className="bg-white border border-gray-200 rounded-xl p-6">
          <div className="flex items-center justify-between mb-3">
            <h3 className="font-semibold text-gray-800">✍️ Optimized Resume</h3>
            <button
              onClick={() =>
                navigator.clipboard.writeText(state.rewrittenResume)
              }
              className="text-xs text-blue-600 hover:text-blue-700 font-medium"
            >
              Copy
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

      {/* Loading state */}
      {state.status === "loading" && !state.rewrittenResume && (
        <div className="flex items-center gap-3 text-sm text-gray-500 p-4">
          <div className="w-4 h-4 border-2 border-blue-500 border-t-transparent rounded-full animate-spin" />
          {loadingMessage}
        </div>
      )}

      {/* Error */}
      {state.error && (
        <div className="bg-red-50 border border-red-200 rounded-xl p-4 text-sm text-red-600">
          ⚠️ {state.error}
        </div>
      )}
    </div>
  );
}
