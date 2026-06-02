import { useState } from "react";
import UploadForm from "./components/UploadForm";
import AnalysisResult from "./components/AnalysisResult";
import type { AnalysisState } from "./types";
import { analyzeResume } from "./api/analyze";

const initialState: AnalysisState = {
  status: "idle",
  jdAnalysis: null,
  matchResult: null,
  suggestions: "",
  rewrittenResume: "",
  error: "",
};

export default function App() {
  const [state, setState] = useState<AnalysisState>(initialState);

  const handleSubmit = async (resume: File, jd: string) => {
    setState({ ...initialState, status: "loading" });

    try {
      await analyzeResume(resume, jd, (step) => {
        if (step.type === "step" && step.step === "jd_analysis") {
          setState((prev) => ({ ...prev, jdAnalysis: step.content }));
        } else if (step.type === "step" && step.step === "match_score") {
          setState((prev) => ({ ...prev, matchResult: step.content }));
        } else if (step.type === "step" && step.step === "suggestions") {
          setState((prev) => ({ ...prev, suggestions: step.content }));
        } else if (step.type === "done") {
          setState((prev) => ({
            ...prev,
            status: "done",
            rewrittenResume: step.content,
          }));
        } else if (step.type === "error") {
          setState((prev) => ({
            ...prev,
            status: "error",
            error: step.message,
          }));
        }
      });
    } catch (err) {
      setState((prev) => ({
        ...prev,
        status: "error",
        error: err instanceof Error ? err.message : "请求失败",
      }));
    }
  };

  return (
    <div className="min-h-screen bg-gray-50">
      <div className="max-w-6xl mx-auto px-4 py-10">
        {/* Header */}
        <div className="mb-8">
          <h1 className="text-2xl font-bold text-gray-900">
            Resume Analyzer AI
          </h1>
          <p className="text-gray-500 mt-1 text-sm">
            上传简历 + 粘贴 JD，AI 分析匹配度并给出针对性优化建议
          </p>
        </div>

        {/* 两栏布局 */}
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          {/* 左栏：输入 */}
          <div className="bg-white border border-gray-200 rounded-xl p-6">
            <UploadForm
              onSubmit={handleSubmit}
              isLoading={state.status === "loading"}
            />
          </div>

          {/* 右栏：结果 */}
          <div>
            {state.status === "idle" ? (
              <div
                className="flex flex-col items-center justify-center h-full
                border border-dashed border-gray-300 rounded-xl p-12 text-center"
              >
                <div className="text-4xl mb-3">🤖</div>
                <p className="text-sm font-medium text-gray-500">等待分析</p>
                <p className="text-xs text-gray-400 mt-1">
                  上传简历并填写 JD 后，AI 将自动分析匹配情况
                </p>
              </div>
            ) : (
              <AnalysisResult state={state} />
            )}
          </div>
        </div>
      </div>
    </div>
  );
}
