import { useState } from "react";
import { Code2, Lock } from "lucide-react";
import { useNavigate } from "react-router-dom";

import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card } from "@/components/ui/card";
import { isSupabaseConfigured, supabase, supabaseConfigMessage } from "@/lib/supabase";

export function LoginPage() {
  const [authError, setAuthError] = useState("");
  const navigate = useNavigate();

  const signIn = async (provider: "google" | "github") => {
    if (!isSupabaseConfigured) {
      setAuthError(supabaseConfigMessage);
      return;
    }

    const { error } = await supabase.auth.signInWithOAuth({
      provider,
      options: {
        redirectTo: `${window.location.origin}/shell`,
      },
    });

    if (error) setAuthError(error.message);
  };

  return (
    <main className="grid min-h-screen bg-slate-50 lg:grid-cols-[1.1fr_0.9fr]">
      <section className="flex items-center bg-[#060a12] px-8 py-12 text-white">
        <div className="mx-auto max-w-xl">
          <Badge className="border-violet-500/30 bg-white/5 text-violet-100">
            Private Resume Workspace
          </Badge>
          <h1 className="mt-6 text-5xl font-bold leading-tight">
            Keep every resume analysis in one secure place.
          </h1>
          <p className="mt-5 text-slate-300">
            Sign in to keep your resume files, job descriptions, reports, and analysis history
            tied to your private account.
          </p>
        </div>
      </section>
      <section className="flex items-center justify-center px-6">
        <Card className="w-full max-w-md p-8">
          <button
            onClick={() => navigate("/")}
            className="mb-8 text-sm text-slate-500 hover:text-slate-900"
          >
            Back to home
          </button>
          <h2 className="text-2xl font-bold text-slate-950">Sign in</h2>
          <p className="mt-2 text-sm text-slate-500">
            Use the provider that matches your developer workflow.
          </p>
          {!isSupabaseConfigured && (
            <div className="mt-6 rounded-lg border border-amber-200 bg-amber-50 px-4 py-3 text-sm leading-6 text-amber-900">
              {supabaseConfigMessage}
            </div>
          )}
          {authError && (
            <div className="mt-6 rounded-lg border border-rose-200 bg-rose-50 px-4 py-3 text-sm leading-6 text-rose-900">
              {authError}
            </div>
          )}
          <div className="mt-8 space-y-3">
            <Button
              variant="outline"
              className="w-full justify-start"
              disabled={!isSupabaseConfigured}
              onClick={() => signIn("google")}
            >
              <Lock className="h-4 w-4" />
              Continue with Google
            </Button>
            <Button
              variant="secondary"
              className="w-full justify-start"
              disabled={!isSupabaseConfigured}
              onClick={() => signIn("github")}
            >
              <Code2 className="h-4 w-4" />
              Continue with GitHub
            </Button>
          </div>
        </Card>
      </section>
    </main>
  );
}
