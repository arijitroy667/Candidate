"use client";

import Link from "next/link";
import { useRouter } from "next/navigation";
import { type ReactNode, useState } from "react";
import { createClient } from "../lib/supabase/client";

type WorkspaceHeaderProps = {
  audience: "candidate" | "company";
  children?: ReactNode;
};

export default function WorkspaceHeader({ audience, children }: WorkspaceHeaderProps) {
  return <header className="mb-8 flex flex-wrap items-center justify-between gap-4 border-b border-[#dfe6de] pb-5"><Link href="/" className="flex items-center gap-3 text-lg font-semibold text-[#1d2725]" aria-label="Return to Candidex landing page"><span className="grid size-9 place-items-center rounded-xl bg-[#173f3a] text-sm text-[#d8f36b]">cx</span><span>candidex</span></Link><div className="flex flex-wrap items-center gap-2"><nav className="flex items-center gap-1 text-sm">{children ?? (audience === "candidate" ? <><Link href="/jobs" className="rounded-lg px-3 py-2 text-[#287067] hover:bg-white">Find jobs</Link><Link href="/jobs?board=institute" className="rounded-lg px-3 py-2 text-[#287067] hover:bg-white">Institute jobs</Link><Link href="/candidate/applications" className="rounded-lg px-3 py-2 text-[#287067] hover:bg-white">Applications</Link></> : <><Link href="/company/jobs" className="rounded-lg px-3 py-2 text-[#287067] hover:bg-white">Jobs</Link><Link href="/company/jobs/new" className="rounded-lg px-3 py-2 text-[#287067] hover:bg-white">Create job</Link></>)}</nav><SignOutButton /></div></header>;
}

export function SignOutButton() {
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");
  const router = useRouter();

  async function signOut() {
    setBusy(true);
    setError("");
    const result = await createClient().auth.signOut();
    if (result.error) {
      setError(result.error.message);
      setBusy(false);
      return;
    }
    router.push("/");
  }

  return <div className="flex items-center gap-2"><button onClick={signOut} disabled={busy} className="rounded-lg border border-[#c3d2c5] bg-white px-3 py-2 text-sm font-medium text-[#315d55] transition hover:border-[#87a52e] disabled:cursor-wait disabled:opacity-60">{busy ? "Signing out..." : "Sign out"}</button>{error && <span className="text-xs text-red-700">{error}</span>}</div>;
}
