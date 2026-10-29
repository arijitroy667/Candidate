"use client";

import Link from "next/link";
import { useParams } from "next/navigation";
import { useEffect, useState } from "react";
import { api, type Job } from "../../../lib/api";
import { createClient } from "../../../lib/supabase/client";

export default function JobDetailPage() {
  const params = useParams<{ id: string }>();
  const [job, setJob] = useState<Job | null>(null);
  const [message, setMessage] = useState("Loading role...");
  useEffect(() => {
    let cancelled = false;
    async function load() {
      try {
        const session = (await createClient().auth.getSession()).data.session;
        const role = String(session?.user.user_metadata?.role ?? "").toUpperCase();
        const item = session && role === "CANDIDATE"
          ? await api.candidateJob(session.access_token, params.id)
          : await api.publicJob(params.id);
        if (!cancelled) { setJob(item); setMessage(""); }
      } catch (error) {
        if (!cancelled) setMessage(error instanceof Error ? error.message : "Role could not be loaded.");
      }
    }
    void load();
    return () => { cancelled = true; };
  }, [params.id]);
  async function apply() {
    const session = (await createClient().auth.getSession()).data.session;
    if (!session) { setMessage("Sign in as a candidate before applying."); return; }
    try { await api.apply(session.access_token, params.id); setMessage("Application submitted. You can track it from your applications."); }
    catch (error) { setMessage(error instanceof Error ? error.message : "Unable to apply."); }
  }
  return <main className="min-h-screen bg-[#f5f7f2] px-6 py-10 text-[#1d2725] lg:px-20"><div className="mx-auto max-w-3xl"><Link href="/jobs" className="text-sm text-[#287067]">← All open roles</Link>{message && !job && <p className="mt-8 rounded-xl border border-[#dfe6de] bg-white p-5 text-sm text-[#6c7973]">{message}</p>}{job && <article className="mt-8 rounded-xl border border-[#dfe6de] bg-white p-8"><p className="text-xs font-semibold uppercase tracking-widest text-[#287067]">{job.target_institute ? `${job.target_institute} campus opportunity` : job.location || "Remote"} · {job.employment_type || "Full-time"}</p><h1 className="mt-3 text-4xl font-semibold">{job.title}</h1><div className="mt-5 flex flex-wrap gap-2">{job.skills.map((skill) => <span key={skill} className="rounded-full bg-[#e7f0e6] px-3 py-1 text-xs text-[#287067]">{skill}</span>)}</div><div className="mt-8 whitespace-pre-wrap text-sm leading-7 text-[#4f5d57]">{job.description}</div><button onClick={apply} className="mt-8 rounded-lg bg-[#173f3a] px-5 py-3 text-sm font-medium text-white">Apply for this role</button>{message && <p className="mt-4 text-sm text-[#287067]">{message}</p>}</article>}</div></main>;
}
