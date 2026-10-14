import { createBrowserClient } from "@supabase/ssr";
import type { SupabaseClient } from "@supabase/supabase-js";

type BrowserClient = SupabaseClient;

const configurationError = new Error(
  "Supabase is not configured. Add NEXT_PUBLIC_SUPABASE_URL and NEXT_PUBLIC_SUPABASE_ANON_KEY to the frontend environment.",
);

const unconfiguredClient = {
  auth: {
    getSession: async () => ({ data: { session: null }, error: configurationError }),
    signInWithPassword: async () => ({ data: { session: null, user: null }, error: configurationError }),
    signUp: async () => ({ data: { session: null, user: null }, error: configurationError }),
  },
} as unknown as BrowserClient;

export function createClient(): BrowserClient {
  const url = process.env.NEXT_PUBLIC_SUPABASE_URL;
  const key = process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY;
  if (!url || !key) return unconfiguredClient;
  return createBrowserClient(
    url,
    key,
  );
}
