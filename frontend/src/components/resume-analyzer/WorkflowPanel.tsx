import { Badge } from "@/components/ui/badge";
import { Card } from "@/components/ui/card";

export function WorkflowPanel({
  step,
  title,
  children,
}: {
  step: string;
  title: string;
  children: React.ReactNode;
}) {
  return (
    <section>
      <div className="mb-4 flex items-center gap-3">
        <Badge className="bg-violet-600 text-white">{step}</Badge>
        <h2 className="text-lg font-bold">{title}</h2>
      </div>
      <Card className="p-8">{children}</Card>
    </section>
  );
}
