import type { Session } from "@supabase/supabase-js";
import {
  FileText,
  History,
  LayoutDashboard,
  LogOut,
  Sparkles,
} from "lucide-react";
import { useLocation, useNavigate } from "react-router-dom";

import { supabase } from "@/lib/supabase";

export function AppShell({
  children,
  session,
}: {
  children: React.ReactNode;
  session: Session;
}) {
  const user = session.user;
  const navigate = useNavigate();
  const location = useLocation();
  const navItems = [
    ["/shell", LayoutDashboard, "New Analysis"],
    ["/shell/history", History, "History"],
    ["/shell/resumes", FileText, "Saved Resumes"],
  ] as const;

  return (
    <main className="min-h-screen bg-slate-50 text-slate-950">
      <aside className="fixed inset-y-0 left-0 hidden w-64 border-r border-slate-200 bg-white p-5 md:flex md:flex-col">
        <div className="mb-8 flex items-center gap-3">
          <div className="flex h-9 w-9 items-center justify-center rounded-full bg-violet-600 text-white">
            <Sparkles className="h-4 w-4" />
          </div>
          <span
            className="cursor-pointer font-semibold"
            onClick={() => navigate("/?intent=landing")}
          >
            Resume Analyzer
          </span>
        </div>
        <nav className="space-y-2">
          {navItems.map(([key, Icon, label]) => (
            <button
              key={key}
              onClick={() => navigate(key)}
              className={`flex w-full items-center gap-3 rounded-lg px-3 py-2 text-sm font-medium transition ${
                location.pathname === key
                  ? "bg-violet-100 text-violet-700"
                  : "text-slate-600 hover:bg-slate-100"
              }`}
            >
              <Icon className="h-4 w-4" />
              {label}
            </button>
          ))}
        </nav>
        <div className="mt-auto rounded-lg border border-slate-200 p-3">
          <p className="truncate text-sm font-semibold">{user.email}</p>
          <button
            className="mt-3 flex items-center gap-2 text-sm text-slate-500 hover:text-slate-950 cursor-pointer"
            onClick={() => {
              supabase.auth.signOut();
              navigate("/");
            }}
          >
            <LogOut className="h-4 w-4" />
            Sign out
          </button>
        </div>
      </aside>
      <section className="md:pl-64">{children}</section>
    </main>
  );
}
