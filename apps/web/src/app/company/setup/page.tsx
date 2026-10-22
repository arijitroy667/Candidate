"use client";

import Link from "next/link";
import { FormEvent, useState } from "react";
import { useRouter } from "next/navigation";
import { api } from "../../../lib/api";
import { createClient } from "../../../lib/supabase/client";
import { AccountActions } from "../../../components/account-actions";

export default function CompanySetupPage() {
  const router = useRouter();
  const [message, setMessage] = useState("");
  async function submit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const values = new FormData(event.currentTarget);
    const session = (await createClient().auth.getSession()).data.session;
    if (!session) { setMessage("Sign in as a company admin first."); return; }
    try {
      await api.createCompany(session.access_token, { name: String(values.get("name")), slug: String(values.get("slug")), website: String(values.get("website") || "") });
      router.push("/company/jobs");
    } catch (error) { setMessage(error instanceof Error ? error.message : "Unable to create company."); }
  }
  return <main className="min-h-screen bg-[#f5f7f2] px-6 py-10 text-[#1d2725] lg:px-20"><div className="mx-auto max-w-xl"><div className="flex items-center justify-between"><Link href="/" className="text-sm text-[#287067]">← Workspace</Link><AccountActions/></div><h1 className="mt-6 text-4xl font-semibold">Set up your company</h1><p className="mt-3 text-[#6c7973]">This creates the workspace where your jobs and candidate reviews live.</p><form onSubmit={submit} className="mt-8 space-y-5 rounded-xl border border-[#dfe6de] bg-white p-6"><Field name="name" label="Company name" required /><Field name="slug" label="Workspace slug" placeholder="acme" required /><Field name="website" label="Website" placeholder="https://example.com" />{message && <p className="text-sm text-red-700">{message}</p>}<button className="rounded-lg bg-[#173f3a] px-5 py-3 text-sm font-medium text-white">Create workspace</button></form></div></main>;
}

function Field({ label, name, placeholder, required }: { label: string; name: string; placeholder?: string; required?: boolean }) { return <label className="block text-sm font-medium">{label}<input name={name} placeholder={placeholder} required={required} className="mt-2 w-full rounded-lg border border-[#dfe6de] p-3" /></label>; }
