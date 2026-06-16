export interface JDAnalysis {
  requirements: string;
  must_skills: string[];
  nice_skills: string[];
}

export interface MatchResult {
  score: number;
  matched: string[];
  missing: string[];
}

export type AnalysisStep =
  | { type: "step"; step: "parsing"; content: string; message: string }
  | { type: "step"; step: "jd_analysis"; content: JDAnalysis; message: string }
  | { type: "step"; step: "match_score"; content: MatchResult; message: string }
  | { type: "step"; step: "suggestions"; content: string; message: string }
  | { type: "done"; content: string; message?: string }
  | { type: "error"; message: string };

export interface AnalysisState {
  status: "idle" | "loading" | "done" | "error";
  jdAnalysis: JDAnalysis | null;
  matchResult: MatchResult | null;
  suggestions: string;
  rewrittenResume: string;
  error: string;
  currentStep: AnalysisStep;
}
