import type { LucideIcon } from "lucide-react";
import {
  CloudUpload,
  Crosshair,
  FileText,
  LineChart,
  PencilLine,
} from "lucide-react";

export interface WorkflowStep {
  title: string;
  description: string;
  icon: LucideIcon;
  details: string[];
}

export const workflowSteps: WorkflowStep[] = [
  {
    title: "Upload resume",
    description: "We securely parse your resume and extract structured information.",
    icon: CloudUpload,
    details: [
      "The original PDF is stored in the user's private workspace.",
      "The backend extracts structured text for analysis.",
      "The file remains available for future history review.",
    ],
  },
  {
    title: "Read job description",
    description: "We analyze the job description to identify requirements and priorities.",
    icon: FileText,
    details: [
      "The job description becomes the comparison baseline.",
      "Role requirements, skills, and seniority signals are extracted.",
      "The analysis is tied to the uploaded resume and user account.",
    ],
  },
  {
    title: "Build match profile",
    description: "We map your skills and experience to the role's required competencies.",
    icon: Crosshair,
    details: [
      "The analysis task runs asynchronously in the FastAPI backend.",
      "Progress is streamed to the frontend through SSE.",
      "The result includes match score, strengths, gaps, and recommendations.",
    ],
  },
  {
    title: "Generate recommendations",
    description: "We surface gaps, strengths, and actionable recommendations.",
    icon: LineChart,
    details: [
      "Completed analyses are saved to the user's history.",
      "The original resume file can be revisited later.",
      "Future report PDFs will be downloadable from the workspace.",
    ],
  },
  {
    title: "Rewrite resume",
    description: "We craft an ATS-friendly, role-aligned resume tailored to the job.",
    icon: PencilLine,
    details: [
      "Rewrite suggestions are tailored to the target role.",
      "The output focuses on clarity, relevance, and measurable impact.",
      "The final result remains connected to the original resume and analysis.",
    ],
  },
];
