"use client";

import Link from "next/link";
import { useEffect, useState } from "react";
import { api, type Job } from "../../../lib/api";
import { createClient } from "../../../lib/supabase/client";

export default function CompanyJobsPage() {
  const [jobs, setJobs] = useState<Job[]>([]);
  const [message, setMessage] = useState("Loading jobs...");
  useEffect(() => {
    createClient().auth.getSession().then(({ data }) => {
      const token = data.session?.access_token;
      if (!token) { setMessage("Sign in as a company user to view jobs."); return; }
      api.companyJobs(token).then((items) => { setJobs(items); setMessage(""); }).catch((error: Error) => setMessage(error.message));
    });
  }, []);
  return <main className="min-h-screen bg-[#f5f7f2] px-6 py-10 text-[#1d2725] lg:px-20"><div className="mx-auto max-w-6xl"><div className="flex items-end justify-between"><div><p className="text-xs font-semibold uppercase tracking-widest text-[#287067]">Company workspace</p><h1 className="mt-2 text-4xl font-semibold">Your jobs</h1></div><div className="flex gap-3"><Link href="/company/setup" className="rounded-lg border border-[#bfcfc2] px-4 py-2.5 text-sm font-medium text-[#287067]">Company profile</Link><Link href="/company/jobs/new" className="rounded-lg bg-[#173f3a] px-4 py-2.5 text-sm font-medium text-white">Create job</Link></div></div>{message && <div className="mt-8 rounded-lg border border-[#dfe6de] bg-white p-4 text-sm text-[#6c7973]"><p>{message}</p><Link href="/company/setup" className="mt-2 inline-block font-medium text-[#287067]">Create or update company profile →</Link></div>}<div className="mt-8 grid gap-4 md:grid-cols-2">{jobs.map((job) => <article key={job.id} className="rounded-xl border border-[#dfe6de] bg-white p-6"><div className="flex items-start justify-between gap-4"><div><h2 className="text-xl font-semibold">{job.title}</h2><p className="mt-1 text-sm text-[#6c7973]">{job.location || "Remote"} · {job.employment_type || "Role"}</p></div><span className="rounded-full bg-[#e7f0e6] px-3 py-1 text-xs text-[#287067]">{job.status}</span></div><p className="mt-4 line-clamp-3 text-sm leading-6 text-[#6c7973]">{job.description}</p><div className="mt-5 flex flex-wrap gap-2">{job.skills.map((skill) => <span key={skill} className="rounded-full bg-[#f5f7f2] px-3 py-1 text-xs text-[#287067]">{skill}</span>)}</div><div className="mt-6 flex gap-4 text-sm"><Link href={`/company/jobs/${job.id}/candidates`} className="font-medium text-[#287067]">Candidates →</Link><Link href={`/company/jobs/${job.id}/edit`} className="text-[#6c7973]">Review setup</Link></div></article>)}</div>{!message && jobs.length === 0 && <div className="mt-8 rounded-xl border border-dashed border-[#bfcfc2] p-10 text-center text-sm text-[#6c7973]">No jobs yet. Create your first role to begin.</div>}</div></main>;
}
