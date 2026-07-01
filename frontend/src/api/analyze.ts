import type { AnalysisStep } from "../types";
import { apiBaseUrl } from "../lib/apiClient";

export async function analyzeResume(
  resume: File,
  jd: string,
  onStep: (step: AnalysisStep) => void,
) {
  const formData = new FormData();
  formData.append("resume", resume);
  formData.append("jd", jd);

  const res = await fetch(`${apiBaseUrl}/api/analyze`, {
    method: "POST",
    body: formData,
  });

  const reader = res.body!.getReader();
  const decoder = new TextDecoder();
  let buffer = "";

  while (true) {
    const { done, value } = await reader.read();
    if (done) break;

    buffer += decoder.decode(value, { stream: true });
    const lines = buffer.split("\n\n");
    buffer = lines.pop() ?? "";

    for (const line of lines) {
      if (!line.startsWith("data: ")) continue;
      try {
        const data = JSON.parse(line.slice(6)) as AnalysisStep;
        onStep(data);
      } catch {
        continue;
      }
    }
  }
}
