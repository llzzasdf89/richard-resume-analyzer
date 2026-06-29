import { apiClient } from "../lib/apiClient";

export interface ResumeItem {
  id: string;
  original_filename: string;
  storage_key: string;
  file_size: number;
  mime_type: string;
  parsed_text: string | null;
  created_at: string;
}

export async function listResumes(): Promise<ResumeItem[]> {
  const response = await apiClient.get("/api/v1/resumes");
  return response.data.data.items;
}

export async function getResume(resumeId: string): Promise<ResumeItem> {
  const response = await apiClient.get(`/api/v1/resumes/${resumeId}`);
  return response.data.data;
}

export async function downloadResumeFile(resumeId: string): Promise<Blob> {
  const response = await apiClient.get(`/api/v1/resumes/${resumeId}/file`, {
    responseType: "blob",
  });
  return response.data;
}

export async function deleteResume(resumeId: string) {
  await apiClient.delete(`/api/v1/resumes/${resumeId}`);
}
