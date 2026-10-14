"use client";

import { FormEvent, useState } from "react";
import { createClient } from "../../lib/supabase/client";

export default function RegisterPage() {
  const [message, setMessage] = useState("");
  async function submit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const values = new FormData(event.currentTarget);
    const result = await createClient().auth.signUp({
      email: String(values.get("email")),
      password: String(values.get("password")),
      options: { data: { full_name: String(values.get("name")), role: String(values.get("role")) } },
    });
    setMessage(result.error?.message ?? "Registration created. Check your email to verify it.");
  }
  return <main className="grid min-h-screen place-items-center bg-[#f5f7f2] px-6"><form onSubmit={submit} className="w-full max-w-md rounded-xl border border-[#dfe6de] bg-white p-8"><p className="text-xs font-semibold uppercase tracking-widest text-[#287067]">Candidex</p><h1 className="mt-3 text-3xl font-semibold">Create your account</h1><label className="mt-8 block text-sm font-medium">Full name<input name="name" required className="mt-2 w-full rounded-lg border border-[#dfe6de] p-3" /></label><label className="mt-4 block text-sm font-medium">Email<input name="email" type="email" required className="mt-2 w-full rounded-lg border border-[#dfe6de] p-3" /></label><label className="mt-4 block text-sm font-medium">I am a<select name="role" className="mt-2 w-full rounded-lg border border-[#dfe6de] p-3"><option value="CANDIDATE">Candidate</option><option value="COMPANY_ADMIN">Company admin</option></select></label><label className="mt-4 block text-sm font-medium">Password<input name="password" type="password" required minLength={8} className="mt-2 w-full rounded-lg border border-[#dfe6de] p-3" /></label><button className="mt-6 w-full rounded-lg bg-[#173f3a] px-4 py-3 font-medium text-white">Register</button>{message && <p className="mt-4 text-sm text-[#287067]">{message}</p>}</form></main>;
}
