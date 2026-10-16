"use client";

import Link from "next/link";
import { Suspense, type FormEvent, useState } from "react";
import { useRouter, useSearchParams } from "next/navigation";
import { createClient } from "../../lib/supabase/client";

export default function LoginPage() {
  return <Suspense fallback={<AuthForm title="Welcome back to your workspace" button="Sign in" message="" onSubmit={() => undefined} />}><LoginContent /></Suspense>;
}

function LoginContent() {
  const [message, setMessage] = useState("");
  const role = useSearchParams().get("role");
  const roleLabel = role === "company" ? "your company workspace" : role === "recruiter" ? "the recruiter workspace" : role === "candidate" ? "your candidate workspace" : "your workspace";
  const router = useRouter();

  async function submit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const values = new FormData(event.currentTarget);
    const result = await createClient().auth.signInWithPassword({
      email: String(values.get("email")),
      password: String(values.get("password")),
    });
    if (result.error) {
      setMessage(result.error.message);
      return;
    }
    setMessage("Signed in successfully. Opening your workspace...");
    const nextRoute = result.data.user?.user_metadata?.role === "CANDIDATE" ? "/candidate/applications" : "/company/jobs";
    router.push(nextRoute);
  }

  return <AuthForm title={`Welcome back to ${roleLabel}`} button="Sign in" message={message} onSubmit={submit} />;
}

function AuthForm({ title, button, message, onSubmit }: { title: string; button: string; message: string; onSubmit: (event: FormEvent<HTMLFormElement>) => void }) {
  return <main className="grid min-h-screen place-items-center bg-[#f7f8f4] px-6"><form onSubmit={onSubmit} className="w-full max-w-md rounded-[24px] border border-[#dfe8dc] bg-white p-8 shadow-[0_20px_60px_rgba(32,71,64,0.09)]"><Link href="/" className="inline-flex items-center gap-2 text-sm font-semibold text-[#315d55]"><span className="grid size-8 place-items-center rounded-lg bg-[#173f3a] text-[10px] text-[#d8f36b]">cx</span>candidex</Link><p className="mt-8 text-xs font-semibold uppercase tracking-widest text-[#87a52e]">Secure access</p><h1 className="mt-3 text-3xl font-semibold tracking-tight text-[#173f3a]">{title}</h1><p className="mt-3 text-sm leading-6 text-[#71817a]">Sign in to continue your hiring or candidate journey.</p><label className="mt-8 block text-sm font-medium text-[#315d55]">Email<input name="email" type="email" required className="mt-2 w-full rounded-xl border border-[#dfe6de] bg-[#fbfcf9] p-3 outline-none transition focus:border-[#87a52e]" /></label><label className="mt-4 block text-sm font-medium text-[#315d55]">Password<input name="password" type="password" required minLength={8} className="mt-2 w-full rounded-xl border border-[#dfe6de] bg-[#fbfcf9] p-3 outline-none transition focus:border-[#87a52e]" /></label><button className="mt-6 w-full rounded-full bg-[#173f3a] px-4 py-3 font-medium text-white transition hover:bg-[#22534c]">{button}</button>{message && <p className="mt-4 rounded-lg bg-[#eef5e5] p-3 text-sm text-[#287067]">{message}</p>}<p className="mt-6 text-center text-sm text-[#71817a]">New to Candidex? <Link href="/register" className="font-semibold text-[#315d55] hover:text-[#87a52e]">Create an account</Link></p></form></main>;
}
