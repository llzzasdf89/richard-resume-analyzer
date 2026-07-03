import { apiClient } from "../lib/apiClient";
import { supabase } from "../lib/supabase";

export interface CreateAnalysisInput {
  resume: File;
  jdText: string;
  jobTitle?: string;
  company?: string;
}

export interface CreateAnalysisResponse {
  analysis_id: string;
  resume_id: string;
  status: string;
}

export interface AnalysisResult {
  score?: number;
  requirements?: string;
  must_skills?: string[];
  nice_skills?: string[];
  matched_skills?: string[];
  missing_skills?: string[];
  suggestions?: string;
  rewritten_resume?: string;
  steps?: Array<{ step: string; status: string }>;
}

export interface AnalysisEvent {
  type: "progress" | "step" | "completed" | "failed";
  analysis_id?: string;
  step?: string;
  status?: string;
  progress?: number;
  score?: number;
  message?: string;
  content?: unknown;
  result?: AnalysisResult;
}

export interface AnalysisListItem {
  id: string;
  resume_id: string;
  status: string;
  score: number | null;
  progress: number;
  current_step: string | null;
  job_title: string | null;
  company: string | null;
  created_at: string;
  updated_at: string;
}

export async function createAnalysis(
  input: CreateAnalysisInput,
  requestId: string,
): Promise<CreateAnalysisResponse> {
  const formData = new FormData();
  formData.append("resume", input.resume);
  formData.append("jd_text", input.jdText);
  if (input.jobTitle) formData.append("job_title", input.jobTitle);
  if (input.company) formData.append("company", input.company);

  const response = await apiClient.post("/api/v1/analyses", formData, {
    headers: { "X-Request-ID": requestId },
  });
  return response.data.data;
}

export async function listAnalyses(): Promise<AnalysisListItem[]> {
  const response = await apiClient.get("/api/v1/analyses");
  return response.data.data.items;
}

export function createAnalysisEventsUrl(analysisId: string) {
  const baseURL = apiClient.defaults.baseURL ?? "";
  return `${baseURL}/api/v1/analyses/${analysisId}/events`;
}

export async function streamAnalysisEvents(
  analysisId: string,
  onEvent: (event: AnalysisEvent) => void,
  signal?: AbortSignal,
) {
  const { data } = await supabase.auth.getSession();
  const token = data.session?.access_token;
  const headers: HeadersInit = {};
  if (token) headers.Authorization = `Bearer ${token}`;

  const response = await fetch(createAnalysisEventsUrl(analysisId), {
    headers,
    signal,
  });
  if (!response.ok) {
    throw new Error("Failed to connect to analysis event stream");
  }
  if (!response.body) {
    throw new Error("Analysis event stream is unavailable");
  }

  const reader = response.body.getReader();
  const decoder = new TextDecoder();
  let buffer = "";

  const processBlock = (block: string) => {
    const dataLines = block
      .split("\n")
      .filter((line) => line.startsWith("data: "))
      .map((line) => line.slice(6));
    if (!dataLines.length) return;
    onEvent(JSON.parse(dataLines.join("\n")) as AnalysisEvent);
  };

  while (true) {
    const { done, value } = await reader.read();
    if (done) break;

    buffer += decoder.decode(value, { stream: true });
    const blocks = buffer.split("\n\n");
    buffer = blocks.pop() ?? "";
    for (const block of blocks) {
      processBlock(block);
    }
  }

  if (buffer.trim()) {
    processBlock(buffer);
  }
}
