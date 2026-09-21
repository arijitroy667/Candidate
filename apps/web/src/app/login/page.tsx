"use client";

import { FormEvent, useState } from "react";
import { createClient } from "../../lib/supabase/client";

export default function LoginPage() {
  const [message, setMessage] = useState("");
  async function submit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const values = new FormData(event.currentTarget);
    const result = await createClient().auth.signInWithPassword({ email: String(values.get("email")), password: String(values.get("password")) });
    setMessage(result.error?.message ?? "Signed in successfully.");
  }
  return <AuthForm title="Welcome back" button="Sign in" message={message} onSubmit={submit} />;
}

function AuthForm({ title, button, message, onSubmit }: { title: string; button: string; message: string; onSubmit: (event: FormEvent<HTMLFormElement>) => void }) {
  return <main className="grid min-h-screen place-items-center bg-[#f5f7f2] px-6"><form onSubmit={onSubmit} className="w-full max-w-md rounded-xl border border-[#dfe6de] bg-white p-8"><p className="text-xs font-semibold uppercase tracking-widest text-[#287067]">Candidex</p><h1 className="mt-3 text-3xl font-semibold">{title}</h1><label className="mt-8 block text-sm font-medium">Email<input name="email" type="email" required className="mt-2 w-full rounded-lg border border-[#dfe6de] p-3" /></label><label className="mt-4 block text-sm font-medium">Password<input name="password" type="password" required minLength={8} className="mt-2 w-full rounded-lg border border-[#dfe6de] p-3" /></label><button className="mt-6 w-full rounded-lg bg-[#173f3a] px-4 py-3 font-medium text-white">{button}</button>{message && <p className="mt-4 text-sm text-[#287067]">{message}</p>}</form></main>;
}