import { apiClient } from "../lib/apiClient";

export async function listResumes() {
  const response = await apiClient.get("/api/v1/resumes");
  return response.data.data.items;
}

export async function getResume(resumeId: string) {
  const response = await apiClient.get(`/api/v1/resumes/${resumeId}`);
  return response.data.data;
}
