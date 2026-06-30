import { createClient } from "@supabase/supabase-js";

const supabaseUrl = import.meta.env.VITE_SUPABASE_URL?.trim() ?? "";
const supabaseAnonKey = import.meta.env.VITE_SUPABASE_ANON_KEY?.trim() ?? "";

export const isSupabaseConfigured = Boolean(supabaseUrl && supabaseAnonKey);

export const supabaseConfigMessage = isSupabaseConfigured
  ? ""
  : "Supabase is not configured. Set VITE_SUPABASE_URL and VITE_SUPABASE_ANON_KEY in frontend/.env, then restart the frontend dev server.";

export const supabase = createClient(
  isSupabaseConfigured ? supabaseUrl : "http://127.0.0.1:54321",
  isSupabaseConfigured ? supabaseAnonKey : "missing-anon-key",
);
