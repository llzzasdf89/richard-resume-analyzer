import { useEffect, useState } from "react";
import { Download, FileText, Trash2 } from "lucide-react";
import { toast } from "sonner";

import {
  deleteResume,
  downloadResumeFile,
  listResumes,
  type ResumeItem,
} from "@/api/resumes";
import { EmptyState } from "@/components/resume-analyzer/EmptyState";
import { Header } from "@/components/resume-analyzer/Header";
import {
  AlertDialog,
  AlertDialogAction,
  AlertDialogCancel,
  AlertDialogContent,
  AlertDialogDescription,
  AlertDialogFooter,
  AlertDialogHeader,
  AlertDialogTitle,
  AlertDialogTrigger,
} from "@/components/ui/alert-dialog";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card } from "@/components/ui/card";
import { Spinner } from "@/components/ui/spinner";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";

export function SavedResumesPage() {
  const [items, setItems] = useState<ResumeItem[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState("");
  const [deletingId, setDeletingId] = useState<string | null>(null);
  const [downloadingId, setDownloadingId] = useState<string | null>(null);

  const refresh = () => {
    setIsLoading(true);
    setError("");
    listResumes()
      .then(setItems)
      .catch((err) => setError(err instanceof Error ? err.message : "Failed to load resumes"))
      .finally(() => setIsLoading(false));
  };

  useEffect(() => {
    refresh();
  }, []);

  const handleDownload = async (resume: ResumeItem) => {
    setDownloadingId(resume.id);
    setError("");
    try {
      const blob = await downloadResumeFile(resume.id);
      const url = URL.createObjectURL(blob);
      const anchor = document.createElement("a");
      anchor.href = url;
      anchor.download = resume.original_filename;
      anchor.click();
      URL.revokeObjectURL(url);
      toast.success("Resume download started", {
        description: resume.original_filename,
      });
    } catch (err) {
      const message = err instanceof Error ? err.message : "Failed to download resume";
      setError(message);
      toast.error("Download failed", {
        description: message,
      });
    } finally {
      setDownloadingId(null);
    }
  };

  const handleDelete = async (resumeId: string) => {
    setDeletingId(resumeId);
    setError("");
    try {
      await deleteResume(resumeId);
      const deletedResume = items.find((item) => item.id === resumeId);
      setItems((currentItems) => currentItems.filter((item) => item.id !== resumeId));
      toast.success("Resume deleted", {
        description: deletedResume?.original_filename ?? "The resume was removed permanently.",
      });
    } catch (err) {
      const message = err instanceof Error ? err.message : "Failed to delete resume";
      setError(message);
      toast.error("Delete failed", {
        description: message,
      });
    } finally {
      setDeletingId(null);
    }
  };

  return (
    <div className="mx-auto max-w-6xl px-6 py-8">
      <Header
        title="Saved Resumes"
        description="Manage original PDF files connected to your analysis reports."
      />
      <Card className="p-6">
        {isLoading && <Spinner className="m-auto size-6"> </Spinner>}
        {!isLoading && error && (
          <div className="mb-4 rounded-lg border border-rose-200 bg-rose-50 px-4 py-3 text-sm text-rose-900">
            {error}
          </div>
        )}
        {!isLoading && items.length === 0 && !error && (
          <EmptyState
            title="No saved resumes yet"
            description="Uploaded PDF resumes will appear here."
          />
        )}
        {!isLoading && items.length > 0 && (
          <Table>
            <TableHeader>
              <TableRow>
                <TableHead>Resume</TableHead>
                <TableHead>Size</TableHead>
                <TableHead>Uploaded</TableHead>
                <TableHead className="text-right">Actions</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {items.map((item) => (
                <TableRow key={item.id}>
                  <TableCell>
                    <div className="flex items-center gap-3">
                      <div className="flex h-9 w-9 items-center justify-center rounded-lg bg-violet-50 text-violet-700">
                        <FileText className="h-4 w-4" />
                      </div>
                      <div>
                        <p className="max-w-md truncate font-medium">{item.original_filename}</p>
                        <div className="mt-1 flex items-center gap-2">
                          <Badge variant="outline">{item.mime_type || "application/pdf"}</Badge>
                          <span className="text-xs text-slate-400">ID: {item.id}</span>
                        </div>
                      </div>
                    </div>
                  </TableCell>
                  <TableCell>{formatBytes(item.file_size)}</TableCell>
                  <TableCell>{formatDate(item.created_at)}</TableCell>
                  <TableCell>
                    <div className="flex justify-end gap-2">
                      <Button
                        variant="outline"
                        size="sm"
                        disabled={downloadingId === item.id}
                        onClick={() => handleDownload(item)}
                      >
                        {downloadingId === item.id ? (
                          <Spinner className="h-4 w-4" />
                        ) : (
                          <Download className="h-4 w-4" />
                        )}
                        Download
                      </Button>
                      <AlertDialog>
                        <AlertDialogTrigger asChild>
                          <Button variant="destructive" size="sm" disabled={deletingId === item.id}>
                            <Trash2 className="h-4 w-4" />
                            Delete
                          </Button>
                        </AlertDialogTrigger>
                        <AlertDialogContent>
                          <AlertDialogHeader>
                            <AlertDialogTitle>Delete this resume?</AlertDialogTitle>
                            <AlertDialogDescription>
                              This action permanently deletes the original resume PDF and related
                              records. It cannot be undone.
                            </AlertDialogDescription>
                          </AlertDialogHeader>
                          <AlertDialogFooter>
                            <AlertDialogCancel>Cancel</AlertDialogCancel>
                            <AlertDialogAction
                              variant="destructive"
                              onClick={() => handleDelete(item.id)}
                            >
                              Delete permanently
                            </AlertDialogAction>
                          </AlertDialogFooter>
                        </AlertDialogContent>
                      </AlertDialog>
                    </div>
                  </TableCell>
                </TableRow>
              ))}
            </TableBody>
          </Table>
        )}
      </Card>
    </div>
  );
}

function formatBytes(value: number) {
  if (!value) return "0 B";
  const units = ["B", "KB", "MB", "GB"];
  const index = Math.min(Math.floor(Math.log(value) / Math.log(1024)), units.length - 1);
  const size = value / 1024 ** index;
  return `${size.toFixed(index === 0 ? 0 : 1)} ${units[index]}`;
}

function formatDate(value: string) {
  return new Intl.DateTimeFormat(undefined, {
    dateStyle: "medium",
    timeStyle: "short",
  }).format(new Date(value));
}
