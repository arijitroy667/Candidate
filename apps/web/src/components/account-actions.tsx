"use client";

import Link from "next/link";
import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { createClient } from "../lib/supabase/client";

export function AccountActions() {
  const router = useRouter();
  const [signedIn, setSignedIn] = useState(false);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");

  useEffect(() => {
    void createClient().auth.getSession().then(({ data }) => setSignedIn(Boolean(data.session)));
  }, []);

  async function signOut() {
    setBusy(true);
    setError("");
    try {
      const result = await createClient().auth.signOut();
      if (result.error) {
        setError(result.error.message);
        setBusy(false);
        return;
      }
      setSignedIn(false);
      router.replace("/login?switch=1");
      router.refresh();
    } catch (reason) {
      setError(reason instanceof Error ? reason.message : "Could not sign out. Try again.");
      setBusy(false);
    }
  }

  if (!signedIn) return <Link href="/login" className="inline-flex h-9 items-center rounded-lg border border-[#dfe6de] bg-white px-3 text-[11px] font-semibold text-[#52635a] hover:bg-[#f3f6f1]">Sign in</Link>;
  return <span className="inline-flex flex-col items-end">
    <button type="button" onClick={() => void signOut()} disabled={busy} className="inline-flex h-9 items-center rounded-lg border border-[#dfe6de] bg-white px-2.5 text-[10px] font-semibold text-[#52635a] transition hover:border-[#c9d6cb] hover:bg-[#f3f6f1] sm:px-3 sm:text-[11px] disabled:opacity-50">{busy ? "Signing out…" : <><span className="sm:hidden">Sign out</span><span className="hidden sm:inline">Sign out / switch account</span></>}</button>
    {error && <span role="status" className="mt-1 max-w-[220px] text-right text-[10px] text-[#9a4a30]">{error}</span>}
  </span>;
}
