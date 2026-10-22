"use client";

import Link from "next/link";
import { FormEvent, useState } from "react";
import { useRouter } from "next/navigation";
import { createClient } from "../../lib/supabase/client";

export default function RegisterPage() {
  const router = useRouter();
  const [message, setMessage] = useState("");
  const [busy, setBusy] = useState(false);

  async function submit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setBusy(true);
    setMessage("");
    const values = new FormData(event.currentTarget);
    try {
      const result = await createClient().auth.signUp({
        email: String(values.get("email")).trim(),
        password: String(values.get("password")),
        options: { data: { full_name: String(values.get("name")).trim(), role: String(values.get("role")) } },
      });
      if (result.error) setMessage(result.error.message);
      else if (result.data.session) { router.replace("/"); router.refresh(); }
      else setMessage("Account created. Verify it from the email we sent, then sign in. You can create another account for a different role.");
    } catch (reason) {
      setMessage(reason instanceof Error ? reason.message : "Unable to create account. Check your connection and try again.");
    } finally {
      setBusy(false);
    }
  }

  return <main className="grid min-h-screen place-items-center bg-[#f5f7f2] px-5 py-10 text-[#1d2725]"><div className="w-full max-w-md"><Link href="/" className="mb-6 inline-flex items-center gap-3"><span className="grid size-10 place-items-center rounded-[14px] bg-[#173f3a] text-sm font-black text-[#d8f36b]">cx</span><span className="text-lg font-semibold tracking-tight">candidex</span></Link><form onSubmit={submit} className="rounded-2xl border border-[#e1e8df] bg-white p-7 shadow-[0_12px_36px_rgba(27,53,41,.06)] md:p-8"><p className="text-[10px] font-bold uppercase tracking-[.17em] text-[#438278]">Get started</p><h1 className="mt-2 text-3xl font-semibold tracking-tight">Create your account</h1><p className="mt-2 text-sm leading-6 text-[#74817a]">Choose the workspace you want this account to use.</p><label className="mt-6 block text-xs font-semibold text-[#52635a]">Full name<input name="name" autoComplete="name" required className="mt-2 w-full rounded-xl border border-[#dfe6de] p-3.5 text-sm font-normal outline-none focus:border-[#73a596] focus:ring-2 focus:ring-[#73a596]/15" placeholder="Your name" /></label><label className="mt-4 block text-xs font-semibold text-[#52635a]">Email<input name="email" type="email" autoComplete="email" required className="mt-2 w-full rounded-xl border border-[#dfe6de] p-3.5 text-sm font-normal outline-none focus:border-[#73a596] focus:ring-2 focus:ring-[#73a596]/15" placeholder="you@example.com" /></label><label className="mt-4 block text-xs font-semibold text-[#52635a]">I’m joining as<select name="role" defaultValue="CANDIDATE" className="mt-2 w-full rounded-xl border border-[#dfe6de] bg-white p-3.5 text-sm font-normal outline-none focus:border-[#73a596]"><option value="CANDIDATE">Candidate</option><option value="COMPANY_ADMIN">Company administrator</option></select></label><p className="mt-2 text-[10px] leading-4 text-[#8a968e]">Institution-only jobs are matched to the email domain on your candidate account. Company administrators can set up their company after signing in.</p><label className="mt-4 block text-xs font-semibold text-[#52635a]">Password<input name="password" type="password" autoComplete="new-password" required minLength={8} className="mt-2 w-full rounded-xl border border-[#dfe6de] p-3.5 text-sm font-normal outline-none focus:border-[#73a596] focus:ring-2 focus:ring-[#73a596]/15" placeholder="At least 8 characters" /></label>{message && <p role="status" className="mt-4 rounded-xl border border-[#e3eadf] bg-[#f5f8f3] p-3 text-xs leading-5 text-[#567166]">{message}</p>}<button disabled={busy} className="mt-6 w-full rounded-xl bg-[#173f3a] px-4 py-3.5 text-sm font-semibold text-white shadow-sm transition hover:bg-[#22574e] disabled:opacity-50">{busy ? "Creating account…" : "Create account"}</button><div className="mt-5 border-t border-[#edf0eb] pt-4 text-center text-xs text-[#7a8780]">Already have an account? <Link href="/login" className="font-semibold text-[#287067] hover:underline">Sign in</Link></div></form></div></main>;
}
