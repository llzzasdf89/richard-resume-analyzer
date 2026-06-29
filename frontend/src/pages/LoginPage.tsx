import { useState } from "react";
import { ChevronLeft, Code2, Mail } from "lucide-react";
import { useNavigate } from "react-router-dom";

import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Separator } from "@/components/ui/separator";
import {
  isSupabaseConfigured,
  supabase,
  supabaseConfigMessage,
} from "@/lib/supabase";

export function LoginPage() {
  const [authError, setAuthError] = useState("");
  const [email, setEmail] = useState("");
  const [emailMessage, setEmailMessage] = useState("");
  const [isSendingEmail, setIsSendingEmail] = useState(false);
  const navigate = useNavigate();

  const signIn = async (provider: "github") => {
    setAuthError("");
    setEmailMessage("");

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

  const signInWithEmail = async () => {
    setAuthError("");
    setEmailMessage("");

    if (!isSupabaseConfigured) {
      setAuthError(supabaseConfigMessage);
      return;
    }

    if (!email.trim()) {
      setAuthError("Enter your email address to continue.");
      return;
    }

    setIsSendingEmail(true);
    const { error } = await supabase.auth.signInWithOtp({
      email: email.trim(),
      options: {
        emailRedirectTo: `${window.location.origin}/shell`,
      },
    });
    setIsSendingEmail(false);

    if (error) {
      setAuthError(error.message);
      return;
    }

    setEmailMessage("Check your inbox for a secure sign-in link.");
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
            Sign in to keep your resume files, job descriptions, reports, and
            analysis history tied to your private account.
          </p>
        </div>
      </section>
      <section className="flex items-center justify-center px-6">
        <Card className="w-full max-w-md p-8">
          <Button
            onClick={() => navigate("/")}
            className="cursor-pointer"
            variant="outline"
          >
            <ChevronLeft />
            Going Back
          </Button>
          <h2 className="text-2xl font-bold text-slate-950">Sign in</h2>
          <div className="space-y-3">
            <Label htmlFor="email">Email address</Label>
            <Input
              id="email"
              type="email"
              value={email}
              autoComplete="email"
              placeholder="you@example.com"
              disabled={!isSupabaseConfigured || isSendingEmail}
              onChange={(event) => setEmail(event.target.value)}
              onKeyDown={(event) => {
                if (event.key === "Enter") {
                  signInWithEmail();
                }
              }}
            />
            <Button
              className="w-full justify-start cursor-pointer"
              disabled={!isSupabaseConfigured || isSendingEmail}
              onClick={signInWithEmail}
            >
              <Mail className="h-4 w-4" />
              {isSendingEmail ? "Sending link..." : "Send verify email"}
            </Button>
          </div>
          {!isSupabaseConfigured && (
            <div className="rounded-lg border border-amber-200 bg-amber-50 px-4 py-3 text-sm leading-6 text-amber-900">
              {supabaseConfigMessage}
            </div>
          )}
          {authError && (
            <div className="rounded-lg border border-rose-200 bg-rose-50 px-4 py-3 text-sm leading-6 text-rose-900">
              {authError}
            </div>
          )}
          {emailMessage && (
            <div className="rounded-lg border border-emerald-200 bg-emerald-50 px-4 py-3 text-sm leading-6 text-emerald-900">
              {emailMessage}
            </div>
          )}
          <div className="space-y-5">
            <div className="flex items-center gap-3">
              <Separator className="flex-1" />
              <span className="text-xs font-medium uppercase tracking-wide text-slate-400">
                Or
              </span>
              <Separator className="flex-1" />
            </div>

            <Button
              variant="secondary"
              className="w-full justify-start cursor-pointer"
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
