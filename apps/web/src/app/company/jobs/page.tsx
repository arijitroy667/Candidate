"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
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
  return <main className="min-h-screen bg-[#f5f7f2] px-6 py-10 text-[#1d2725] lg:px-20"><div className="mx-auto max-w-5xl"><p className="text-xs font-semibold uppercase tracking-widest text-[#287067]">Company workspace</p><div className="mt-2 flex items-end justify-between"><h1 className="text-4xl font-semibold">Your jobs</h1><Link href="/" className="rounded-lg bg-[#173f3a] px-4 py-2.5 text-sm font-medium text-white">Dashboard</Link></div>{message && <p className="mt-8 text-sm text-[#6c7973]">{message}</p>}<div className="mt-8 grid gap-4 md:grid-cols-2">{jobs.map((job) => <article key={job.id} className="rounded-xl border border-[#dfe6de] bg-white p-6"><div className="flex items-start justify-between"><h2 className="text-xl font-semibold">{job.title}</h2><span className="rounded-full bg-[#e7f0e6] px-3 py-1 text-xs text-[#287067]">{job.status}</span></div><p className="mt-3 line-clamp-3 text-sm leading-6 text-[#6c7973]">{job.description}</p><p className="mt-5 text-xs text-[#82908a]">{job.location || "Remote"} · {job.skills.join(", ") || "No skills configured"}</p></article>)}</div></div></main>;
}
