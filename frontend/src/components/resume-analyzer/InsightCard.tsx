import { CheckCircle2, CircleAlert } from "lucide-react";

import { Card } from "@/components/ui/card";

export function InsightCard({
  title,
  items,
  tone = "positive",
}: {
  title: string;
  items: string[];
  tone?: "positive" | "gap";
}) {
  const Icon = tone === "gap" ? CircleAlert : CheckCircle2;
  const iconColor = tone === "gap" ? "text-amber-500" : "text-emerald-500";

  return (
    <Card className="p-5">
      <h3 className="font-semibold">{title}</h3>
      {(items?.length && (
        <ul className="mt-4 space-y-3 text-sm text-slate-600">
          {items.map((item) => (
            <li key={item} className="flex gap-2">
              <Icon className={`mt-0.5 h-4 w-4 ${iconColor}`} />
              <span>{item}</span>
            </li>
          ))}
        </ul>
      )) || (
        <p className="mt-4 text-sm text-slate-600">
          No {title.toLowerCase()} found
        </p>
      )}
    </Card>
  );
}
