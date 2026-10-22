"use client";

import Link from "next/link";
import { FormEvent, useState } from "react";
import { useRouter } from "next/navigation";
import { createClient } from "../../lib/supabase/client";

export default function LoginPage() {
  const router = useRouter();
  const [message, setMessage] = useState("");
  const [busy, setBusy] = useState(false);

  async function submit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setBusy(true);
    setMessage("");
    const values = new FormData(event.currentTarget);
    try {
      const result = await createClient().auth.signInWithPassword({ email: String(values.get("email")).trim(), password: String(values.get("password")) });
      if (result.error) setMessage(result.error.message);
      else if (result.data.session) { router.replace("/"); router.refresh(); }
      else setMessage("Check your email to verify your account, then sign in again.");
    } catch (reason) {
      setMessage(reason instanceof Error ? reason.message : "Unable to sign in. Check your connection and try again.");
    } finally {
      setBusy(false);
    }
  }

  return <main className="grid min-h-screen place-items-center bg-[#f5f7f2] px-5 py-10 text-[#1d2725]"><div className="w-full max-w-md"><Link href="/" className="mb-6 inline-flex items-center gap-3"><span className="grid size-10 place-items-center rounded-[14px] bg-[#173f3a] text-sm font-black text-[#d8f36b]">cx</span><span className="text-lg font-semibold tracking-tight">candidex</span></Link><form onSubmit={submit} className="rounded-2xl border border-[#e1e8df] bg-white p-7 shadow-[0_12px_36px_rgba(27,53,41,.06)] md:p-8"><p className="text-[10px] font-bold uppercase tracking-[.17em] text-[#438278]">Welcome back</p><h1 className="mt-2 text-3xl font-semibold tracking-tight">Sign in to your workspace</h1><p className="mt-2 text-sm leading-6 text-[#74817a]">Use the account you registered as a candidate or company administrator.</p><label className="mt-7 block text-xs font-semibold text-[#52635a]">Email<input name="email" type="email" autoComplete="email" required className="mt-2 w-full rounded-xl border border-[#dfe6de] bg-white p-3.5 text-sm font-normal outline-none transition focus:border-[#73a596] focus:ring-2 focus:ring-[#73a596]/15" placeholder="you@example.com" /></label><label className="mt-4 block text-xs font-semibold text-[#52635a]">Password<input name="password" type="password" autoComplete="current-password" required minLength={8} className="mt-2 w-full rounded-xl border border-[#dfe6de] bg-white p-3.5 text-sm font-normal outline-none transition focus:border-[#73a596] focus:ring-2 focus:ring-[#73a596]/15" placeholder="Your password" /></label>{message && <p role="status" className="mt-4 rounded-xl border border-[#f2c8b9] bg-[#fff8f5] p-3 text-xs leading-5 text-[#9a4a30]">{message}</p>}<button disabled={busy} className="mt-6 w-full rounded-xl bg-[#173f3a] px-4 py-3.5 text-sm font-semibold text-white shadow-sm transition hover:bg-[#22574e] disabled:opacity-50">{busy ? "Signing in…" : "Sign in"}</button><div className="mt-5 border-t border-[#edf0eb] pt-4 text-center text-xs text-[#7a8780]"><span>New here? </span><Link href="/register" className="font-semibold text-[#287067] hover:underline">Create a candidate or company account</Link></div><p className="mt-3 text-center text-[10px] leading-4 text-[#98a29b]">To switch roles, sign out and sign in with the separate account for that role.</p></form></div></main>;
}
