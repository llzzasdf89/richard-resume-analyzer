import { useEffect, useState } from "react";

import { listAnalyses, type AnalysisListItem } from "@/api/analyses";
import { EmptyState } from "@/components/resume-analyzer/EmptyState";
import { Header } from "@/components/resume-analyzer/Header";
import { Badge } from "@/components/ui/badge";
import { Card } from "@/components/ui/card";
import { Progress } from "@/components/ui/progress";
import { Spinner } from "@/components/ui/spinner";

export function HistoryPage() {
  const [items, setItems] = useState<AnalysisListItem[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState("");

  useEffect(() => {
    let isMounted = true;

    listAnalyses()
      .then((nextItems) => {
        if (isMounted) setItems(nextItems);
      })
      .catch((err) => {
        if (isMounted) {
          setError(err instanceof Error ? err.message : "Failed to load history");
        }
      })
      .finally(() => {
        if (isMounted) setIsLoading(false);
      });

    return () => {
      isMounted = false;
    };
  }, []);

  return (
    <div className="mx-auto max-w-6xl px-6 py-8">
      <Header title="History" description="Review previous resume analyses and reports." />
      <Card className="p-6">
        {isLoading && <Spinner className="m-auto size-6"> </Spinner>}
        {!isLoading && error && <EmptyState title="Unable to load history" description={error} />}
        {!isLoading && !error && items.length === 0 && (
          <EmptyState
            title="No analysis history yet"
            description="Run your first resume analysis to see it here."
          />
        )}
        {!isLoading && !error && items.length > 0 && (
          <div className="divide-y divide-slate-100">
            {items.map((item) => (
              <div
                key={item.id}
                className="flex flex-col gap-4 py-5 md:flex-row md:items-center md:justify-between"
              >
                <div>
                  <div className="flex flex-wrap items-center gap-3">
                    <h2 className="font-semibold">{item.job_title || "Untitled role"}</h2>
                    <Badge className={statusBadgeClass(item.status)}>{item.status}</Badge>
                  </div>
                  <p className="mt-1 text-sm text-slate-500">
                    {item.company || "No company"} · {formatDate(item.created_at)}
                  </p>
                  <p className="mt-2 text-xs text-slate-400">Analysis ID: {item.id}</p>
                </div>
                <div className="flex items-center gap-6">
                  <div className="text-right">
                    <p className="text-sm text-slate-500">Score</p>
                    <p className="text-2xl font-bold">
                      {item.score ?? "--"}
                      {item.score !== null ? "%" : ""}
                    </p>
                  </div>
                  <div className="w-36">
                    <Progress value={item.progress} />
                    <p className="mt-2 text-xs text-slate-500">
                      {item.current_step || "waiting"}
                    </p>
                  </div>
                </div>
              </div>
            ))}
          </div>
        )}
      </Card>
    </div>
  );
}

function statusBadgeClass(status: string) {
  if (status === "completed") return "border-emerald-200 bg-emerald-50 text-emerald-700";
  if (status === "failed") return "border-rose-200 bg-rose-50 text-rose-700";
  if (status === "processing") return "border-violet-200 bg-violet-50 text-violet-700";
  return "border-slate-200 bg-slate-50 text-slate-600";
}

function formatDate(value: string) {
  return new Intl.DateTimeFormat(undefined, {
    dateStyle: "medium",
    timeStyle: "short",
  }).format(new Date(value));
}
