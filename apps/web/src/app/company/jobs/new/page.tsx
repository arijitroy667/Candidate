"use client";

import Link from "next/link";
import { FormEvent, useState } from "react";
import { useRouter } from "next/navigation";
import { api } from "../../../../lib/api";
import { createClient } from "../../../../lib/supabase/client";
import { AccountActions } from "../../../../components/account-actions";

export default function NewJobPage() {
  const router = useRouter();
  const [message, setMessage] = useState("");
  const [busy, setBusy] = useState(false);
  const [instituteOnly, setInstituteOnly] = useState(false);
  async function submit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault(); setBusy(true); setMessage("");
    const values = new FormData(event.currentTarget);
    const session = (await createClient().auth.getSession()).data.session;
    if (!session) { setMessage("Sign in before creating a job."); setBusy(false); return; }
    try {
      const job = await api.createJob(session.access_token, {
        title: String(values.get("title")), description: String(values.get("description")),
        department: String(values.get("department") || "") || null, location: String(values.get("location") || "") || null,
        employment_type: String(values.get("employment_type") || "") || null,
        target_institute: instituteOnly ? String(values.get("target_institute") || "").trim() : null,
        target_email_domain: instituteOnly ? String(values.get("target_email_domain") || "").trim().toLowerCase().replace(/^@/, "") : null,
        skills: String(values.get("skills") || "").split(",").map((item) => item.trim()).filter(Boolean),
      });
      await api.analyzeJob(session.access_token, job.id);
      setMessage("Job created and requirements analyzed. Publishing it now...");
      await api.publishJob(session.access_token, job.id);
      router.push("/company/jobs");
    } catch (error) { setMessage(error instanceof Error ? error.message : "Unable to create job."); }
    finally { setBusy(false); }
  }
  return <main className="min-h-screen bg-[#f5f7f2] px-6 py-10 text-[#1d2725] lg:px-20"><div className="mx-auto max-w-3xl"><div className="flex items-center justify-between"><Link href="/company/jobs" className="text-sm text-[#287067]">← Back to jobs</Link><AccountActions/></div><p className="mt-7 text-xs font-semibold uppercase tracking-[.16em] text-[#438278]">Company workspace</p><h1 className="mt-2 text-4xl font-semibold tracking-tight">Create a hiring role</h1><p className="mt-3 text-[#6c7973]">Set your role details, then choose where candidates can discover it.</p><form onSubmit={submit} className="mt-8 space-y-5 rounded-2xl border border-[#dfe6de] bg-white p-6 shadow-sm md:p-8"><Field label="Job title" name="title" required /><div className="grid gap-5 sm:grid-cols-2"><Field label="Department" name="department" /><Field label="Location" name="location" placeholder="Remote" /></div><div className="grid gap-5 sm:grid-cols-2"><Field label="Employment type" name="employment_type" placeholder="Full-time" /><Field label="Skills" name="skills" placeholder="Python, FastAPI, PostgreSQL" /></div><label className="block text-sm font-medium">Who can see this role?<select name="audience" value={instituteOnly ? "INSTITUTE" : "PUBLIC"} onChange={(event) => setInstituteOnly(event.target.value === "INSTITUTE")} className="mt-2 w-full rounded-lg border border-[#dfe6de] bg-white p-3"><option value="PUBLIC">Public job board · everyone</option><option value="INSTITUTE">Students at a specific institute</option></select><span className="mt-1.5 block text-xs font-normal text-[#7e8b83]">Institute roles are shown only to signed-in candidates whose email domain matches the institute.</span></label>{instituteOnly && <div className="grid gap-4 rounded-xl bg-[#f6f8f4] p-4 sm:grid-cols-2"><Field label="Institute or organization" name="target_institute" required placeholder="Example Institute of Technology"/><Field label="Student email domain" name="target_email_domain" required placeholder="students.example.edu"/><p className="text-[10px] leading-4 text-[#7e8b83] sm:col-span-2">Enter the domain after @. Candidates must sign in with that email domain to view and apply.</p></div>}<label className="block text-sm font-medium">Job description<textarea name="description" required minLength={20} rows={10} className="mt-2 w-full rounded-lg border border-[#dfe6de] p-3" placeholder="Describe the role, responsibilities, and experience required." /></label>{message && <p className="rounded-lg bg-[#f5f7f2] p-3 text-sm text-[#287067]">{message}</p>}<div className="flex flex-wrap items-center justify-between gap-3 border-t border-[#edf0eb] pt-5"><p className="text-xs text-[#7e8b83]">Requirements will be analyzed before publishing.</p><button disabled={busy} className="rounded-xl bg-[#173f3a] px-5 py-3 text-sm font-semibold text-white shadow-sm transition hover:bg-[#22574e] disabled:opacity-50">{busy ? "Creating…" : "Create and publish"}</button></div></form></div></main>;
}

function Field({ label, name, required, placeholder }: { label: string; name: string; required?: boolean; placeholder?: string }) {
  return <label className="block text-sm font-medium">{label}<input name={name} required={required} placeholder={placeholder} className="mt-2 w-full rounded-lg border border-[#dfe6de] p-3" /></label>;
}
