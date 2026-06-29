import { apiClient } from "../lib/apiClient";

export async function getReport(reportId: string) {
  const response = await apiClient.get(`/api/v1/reports/${reportId}`);
  return response.data.data;
}
