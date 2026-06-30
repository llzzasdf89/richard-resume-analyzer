import { Sparkles } from "lucide-react";
import { Outlet, useLocation, useNavigate } from "react-router-dom";

import { Button } from "@/components/ui/button";

export function PublicLayout() {
  const navigate = useNavigate();
  const location = useLocation();
  const isWorkflow = location.pathname === "/workflow";

  return (
    <main className="min-h-screen bg-slate-50 text-slate-950">
      <section className="bg-[#060a12] text-white">
        <header className="mx-auto flex max-w-7xl items-center justify-between px-6 py-6">
          <button
            type="button"
            className="flex cursor-pointer items-center gap-3 text-left"
            onClick={() => navigate("/?intent=landing")}
          >
            <div className="flex h-9 w-9 items-center justify-center rounded-full bg-violet-600">
              <Sparkles className="h-4 w-4" />
            </div>
            <span className="font-semibold">Resume Analyzer</span>
          </button>

          <nav className="hidden items-center gap-8 text-sm text-slate-300 md:flex">
            <button
              type="button"
              onClick={() => navigate("/?intent=landing")}
              className={
                !isWorkflow
                  ? "font-semibold text-white cursor-pointer"
                  : "hover:text-white cursor-pointer"
              }
            >
              Features
            </button>
            <button
              type="button"
              onClick={() => navigate("/workflow")}
              className={
                isWorkflow
                  ? "font-semibold text-white cursor-pointer"
                  : "hover:text-white cursor-pointer"
              }
            >
              How It Works
            </button>
          </nav>

          <Button onClick={() => navigate("/login")} className="cursor-pointer">
            Get Started
          </Button>
        </header>

        <Outlet />
      </section>
    </main>
  );
}
