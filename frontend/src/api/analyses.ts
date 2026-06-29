import { apiClient } from "../lib/apiClient";

export interface CreateAnalysisInput {
  resume: File;
  jdText: string;
  jobTitle?: string;
  company?: string;
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

export async function createAnalysis(input: CreateAnalysisInput, requestId: string) {
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
