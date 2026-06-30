import { CheckCircle2 } from "lucide-react";

import { Card } from "@/components/ui/card";

export function InsightCard({ title, items }: { title: string; items: string[] }) {
  return (
    <Card className="p-5">
      <h3 className="font-semibold">{title}</h3>
      <ul className="mt-4 space-y-3 text-sm text-slate-600">
        {items.map((item) => (
          <li key={item} className="flex gap-2">
            <CheckCircle2 className="mt-0.5 h-4 w-4 text-emerald-500" />
            <span>{item}</span>
          </li>
        ))}
      </ul>
    </Card>
  );
}
