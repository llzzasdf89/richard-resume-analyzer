import { useEffect, useRef, useState } from "react";
import type { Session } from "@supabase/supabase-js";
import {
  Navigate,
  Route,
  Routes,
  useLocation,
  useNavigate,
} from "react-router-dom";

import { Spinner } from "@/components/ui/spinner";
import { AppShell } from "@/layout/AppShell";
import { PublicLayout } from "@/layout/PublicLayout";
import { isSupabaseConfigured, supabase } from "@/lib/supabase";
import { HistoryPage } from "@/pages/HistoryPage";
import { LandingPage } from "@/pages/LandingPage";
import { LoginPage } from "@/pages/LoginPage";
import { NewAnalysisPage } from "@/pages/NewAnalysisPage";
import { SavedResumesPage } from "@/pages/SavedResumesPage";
import { WorkflowPage } from "@/pages/WorkflowPage";

export function AppRoutes() {
  const [session, setSession] = useState<Session | null>(null);
  const [isLoadingSession, setIsLoadingSession] = useState(true);
  const navigate = useNavigate();
  const location = useLocation();
  const locationRef = useRef({
    pathname: location.pathname,
    search: location.search,
  });

  useEffect(() => {
    locationRef.current = {
      pathname: location.pathname,
      search: location.search,
    };
  }, [location.pathname, location.search]);

  useEffect(() => {
    if (!isSupabaseConfigured) {
      setIsLoadingSession(false);
      return;
    }

    supabase.auth.getSession().then(({ data }) => {
      setSession(data.session);
      setIsLoadingSession(false);
      if (data.session && shouldRedirectAuthenticatedUser(locationRef.current)) {
        navigate("/shell", { replace: true });
      }
    });

    const { data } = supabase.auth.onAuthStateChange((_event, nextSession) => {
      setSession(nextSession);
      if (nextSession && shouldRedirectAuthenticatedUser(locationRef.current)) {
        navigate("/shell", { replace: true });
      }
    });

    return () => data.subscription.unsubscribe();
  }, [navigate]);

  return (
    <Routes>
      <Route element={<PublicLayout />}>
        <Route path="/" element={<LandingPage />} />
        <Route path="/workflow" element={<WorkflowPage />} />
      </Route>
      <Route path="/login" element={<LoginPage />} />
      <Route
        path="/shell"
        element={
          <ProtectedShell session={session} isLoadingSession={isLoadingSession}>
            <NewAnalysisPage />
          </ProtectedShell>
        }
      />
      <Route
        path="/shell/history"
        element={
          <ProtectedShell session={session} isLoadingSession={isLoadingSession}>
            <HistoryPage />
          </ProtectedShell>
        }
      />
      <Route
        path="/shell/resumes"
        element={
          <ProtectedShell session={session} isLoadingSession={isLoadingSession}>
            <SavedResumesPage />
          </ProtectedShell>
        }
      />
      <Route path="*" element={<Navigate to="/" replace />} />
    </Routes>
  );
}

function ProtectedShell({
  children,
  session,
  isLoadingSession,
}: {
  children: React.ReactNode;
  session: Session | null;
  isLoadingSession: boolean;
}) {
  if (isLoadingSession) {
    return (
      <main className="flex min-h-screen items-center justify-center bg-slate-50 text-slate-600">
        <Spinner />
      </main>
    );
  }

  if (!session) {
    return <Navigate to="/login" replace />;
  }

  return <AppShell session={session}>{children}</AppShell>;
}

function shouldRedirectAuthenticatedUser(location: { pathname: string; search: string }) {
  if (location.pathname === "/login") return true;
  if (location.pathname !== "/") return false;

  return new URLSearchParams(location.search).get("intent") !== "landing";
}
