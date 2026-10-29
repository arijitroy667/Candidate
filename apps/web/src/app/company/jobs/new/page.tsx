"use client";

import Link from "next/link";
import { type FormEvent, useState } from "react";
import { useRouter } from "next/navigation";
import { api } from "../../../../lib/api";
import { createClient } from "../../../../lib/supabase/client";
import WorkspaceHeader from "../../../../components/workspace-header";

export default function NewJobPage() {
  const router = useRouter();
  const [message, setMessage] = useState("");
  const [busy, setBusy] = useState(false);
  const [instituteOnly, setInstituteOnly] = useState(false);

  async function submit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setBusy(true);
    setMessage("");
    const values = new FormData(event.currentTarget);
    const session = (await createClient().auth.getSession()).data.session;
    if (!session) {
      setMessage("Sign in before creating a job.");
      setBusy(false);
      return;
    }
    try {
      const job = await api.createJob(session.access_token, {
        title: String(values.get("title")),
        description: String(values.get("description")),
        department: String(values.get("department") || "") || null,
        location: String(values.get("location") || "") || null,
        employment_type: String(values.get("employment_type") || "") || null,
        skills: String(values.get("skills") || "").split(",").map((item) => item.trim()).filter(Boolean),
        target_institute: instituteOnly ? String(values.get("target_institute") || "").trim() : null,
        target_email_domain: instituteOnly ? String(values.get("target_email_domain") || "").trim().toLowerCase().replace(/^@/, "") : null,
      });
      await api.analyzeJob(session.access_token, job.id);
      setMessage("Job created and requirements analyzed. Publishing it now...");
      await api.publishJob(session.access_token, job.id);
      router.push("/company/jobs");
    } catch (error) {
      setMessage(error instanceof Error ? error.message : "Unable to create job.");
    } finally {
      setBusy(false);
    }
  }

  return <main className="min-h-screen bg-[#f5f7f2] px-6 py-8 text-[#1d2725] lg:px-20"><div className="mx-auto max-w-3xl"><WorkspaceHeader audience="company" /><Link href="/company/jobs" className="text-sm text-[#287067]">← Back to jobs</Link><h1 className="mt-6 text-4xl font-semibold">Create a hiring role</h1><p className="mt-3 text-[#6c7973]">Add the role details. Candidex will extract initial requirements, which your team can refine before using screening.</p><form onSubmit={submit} className="mt-8 space-y-5 rounded-xl border border-[#dfe6de] bg-white p-6"><Field label="Job title" name="title" required /><div className="grid gap-5 sm:grid-cols-2"><Field label="Department" name="department" /><Field label="Location" name="location" placeholder="Remote" /></div><Field label="Employment type" name="employment_type" placeholder="Full-time" /><Field label="Skills" name="skills" placeholder="Python, FastAPI, PostgreSQL" /><label className="block text-sm font-medium">Who can see this role?<select value={instituteOnly ? "INSTITUTE" : "PUBLIC"} onChange={(event) => setInstituteOnly(event.target.value === "INSTITUTE")} className="mt-2 w-full rounded-lg border border-[#dfe6de] bg-white p-3"><option value="PUBLIC">Public — all candidates</option><option value="INSTITUTE">Institute students only</option></select><span className="mt-1 block text-xs font-normal text-[#6c7973]">Institute roles are visible only to candidates signed in with that institute’s email domain.</span></label>{instituteOnly && <div className="grid gap-4 rounded-xl bg-[#f5f7f2] p-4 sm:grid-cols-2"><Field label="Institute name" name="target_institute" required placeholder="Example University"/><Field label="Student email domain" name="target_email_domain" required placeholder="students.example.edu"/><p className="text-xs leading-5 text-[#6c7973] sm:col-span-2">Enter the part after @. Any institute can use this feature.</p></div>}<label className="block text-sm font-medium">Job description<textarea name="description" required minLength={20} rows={12} className="mt-2 w-full rounded-lg border border-[#dfe6de] p-3" placeholder="Describe the role, responsibilities, and experience required." /></label>{message && <p className="rounded-lg bg-[#f5f7f2] p-3 text-sm text-[#287067]">{message}</p>}<button disabled={busy} className="rounded-lg bg-[#173f3a] px-5 py-3 text-sm font-medium text-white disabled:opacity-50">{busy ? "Creating..." : "Create and publish"}</button></form></div></main>;
}

function Field({ label, name, required, placeholder }: { label: string; name: string; required?: boolean; placeholder?: string }) {
  return <label className="block text-sm font-medium">{label}<input name={name} required={required} placeholder={placeholder} className="mt-2 w-full rounded-lg border border-[#dfe6de] p-3" /></label>;
}
