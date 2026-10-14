"use client";

import Link from "next/link";
import { useEffect, useState } from "react";
import { api, type Job } from "../lib/api";
import { createClient } from "../lib/supabase/client";

export default function Home() {
  const [jobs, setJobs] = useState<Job[]>([]);
  const [message, setMessage] = useState("Loading your workspace...");
  const [role, setRole] = useState<string | null>(null);

  useEffect(() => {
    const client = createClient();
    client.auth.getSession().then(({ data }) => {
      const session = data.session;
      if (!session) { setMessage("Sign in to open your workspace."); return; }
      setRole(session.user.user_metadata?.role ?? "CANDIDATE");
      if (session.user.user_metadata?.role === "CANDIDATE") {
        setMessage("Your candidate workspace is ready.");
        return;
      }
      api.companyJobs(session.access_token)
        .then((items) => { setJobs(items); setMessage(""); })
        .catch((error: Error) => setMessage(error.message));
    });
  }, []);

  const isCandidate = role === "CANDIDATE";
  return (
    <main className="min-h-screen bg-[#f5f7f2] px-6 py-8 text-[#1d2725] lg:px-12">
      <div className="mx-auto max-w-6xl">
        <header className="flex items-center justify-between border-b border-[#dfe6de] pb-6">
          <div className="flex items-center gap-3 text-lg font-semibold"><span className="grid size-9 place-items-center rounded-xl bg-[#173f3a] text-sm text-[#d8f36b]">cx</span>candidex</div>
          <nav className="flex items-center gap-3 text-sm">
            <Link href={isCandidate ? "/jobs" : "/company/jobs"} className="rounded-lg px-3 py-2 text-[#287067]">{isCandidate ? "Find jobs" : "Jobs"}</Link>
            <Link href={isCandidate ? "/candidate/applications" : "/company/jobs/new"} className="rounded-lg bg-[#173f3a] px-4 py-2.5 font-medium text-white">{isCandidate ? "My applications" : "Create job"}</Link>
          </nav>
        </header>
        <section className="mt-12">
          <p className="text-xs font-semibold uppercase tracking-[0.18em] text-[#82908a]">{isCandidate ? "Candidate workspace" : "Recruiter workspace"}</p>
          <h1 className="mt-2 text-4xl font-semibold tracking-tight">Human-led hiring, with useful evidence.</h1>
          <p className="mt-3 max-w-2xl text-[#6c7973]">Candidex keeps screening structured and explainable so people make the final hiring decision.</p>
        </section>
        {message && <p className="mt-8 rounded-xl border border-[#dfe6de] bg-white p-5 text-sm text-[#6c7973]">{message}</p>}
        {!isCandidate && !message && <section className="mt-8 grid gap-4 sm:grid-cols-3">
          <Metric label="Active jobs" value={String(jobs.filter((job) => job.status === "PUBLISHED").length)} />
          <Metric label="Draft jobs" value={String(jobs.filter((job) => job.status === "DRAFT").length)} />
          <Metric label="Total roles" value={String(jobs.length)} />
        </section>}
        {!isCandidate && !message && <section className="mt-8 rounded-xl border border-[#dfe6de] bg-white p-6">
          <div className="flex items-center justify-between"><div><h2 className="font-semibold">Your hiring roles</h2><p className="mt-1 text-sm text-[#6c7973]">Create a job, confirm requirements, and publish it for candidates.</p></div><Link href="/company/jobs" className="text-sm font-medium text-[#287067]">View all →</Link></div>
          <div className="mt-6 space-y-3">{jobs.slice(0, 5).map((job) => <div key={job.id} className="flex items-center justify-between rounded-lg bg-[#f5f7f2] p-4"><div><p className="font-medium">{job.title}</p><p className="mt-1 text-xs text-[#6c7973]">{job.location || "Remote"} · {job.skills.join(", ") || "No skills configured"}</p></div><span className="rounded-full bg-[#e7f0e6] px-3 py-1 text-xs font-medium text-[#287067]">{job.status}</span></div>)}</div>
        </section>}
      </div>
    </main>
  );
}

function Metric({ label, value }: { label: string; value: string }) {
  return <div className="rounded-xl border border-[#dfe6de] bg-white p-5"><p className="text-sm text-[#6c7973]">{label}</p><p className="mt-3 text-3xl font-semibold">{value}</p></div>;
}
