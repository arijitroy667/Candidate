"use client";

import Link from "next/link";
import { useEffect, useState } from "react";
import { api, type Job } from "../../../lib/api";
import { createClient } from "../../../lib/supabase/client";
import { AccountActions } from "../../../components/account-actions";

export default function CompanyJobsPage() {
  const [jobs, setJobs] = useState<Job[]>([]);
  const [counts, setCounts] = useState<Record<string, number>>({});
  const [message, setMessage] = useState("Loading your roles…");

  useEffect(() => {
    let cancelled = false;
    void (async () => {
      try {
        const session = (await createClient().auth.getSession()).data.session;
        if (!session) { setMessage("Sign in as a company user to view your roles."); return; }
        const items = await api.companyJobs(session.access_token);
        if (cancelled) return;
        setJobs(items);
        setMessage("");
        const results = await Promise.all(items.map(async (job) => {
          try { return [job.id, (await api.jobCandidates(session.access_token, job.id)).length] as const; }
          catch { return [job.id, 0] as const; }
        }));
        if (!cancelled) setCounts(Object.fromEntries(results));
      } catch (error) {
        if (!cancelled) setMessage(error instanceof Error ? error.message : "Your roles could not be loaded.");
      }
    })();
    return () => { cancelled = true; };
  }, []);

  const applicantTotal = Object.values(counts).reduce((sum, value) => sum + value, 0);
  const published = jobs.filter((job) => job.status === "PUBLISHED").length;

  return <main className="min-h-screen bg-[#f5f7f2] text-[#1d2725]"><header className="border-b border-[#e5ebe3] bg-white"><div className="mx-auto flex h-[72px] max-w-6xl items-center justify-between px-5 md:px-8"><Link href="/" className="flex items-center gap-3"><span className="grid size-9 place-items-center rounded-xl bg-[#173f3a] text-xs font-black text-[#d8f36b]">cx</span><span className="font-semibold">candidex</span></Link><div className="flex items-center gap-3"><Link href="/" className="text-xs font-semibold text-[#52635a] hover:text-[#287067]">← Workspace</Link><AccountActions/></div></div></header>
    <div className="mx-auto max-w-6xl px-5 py-9 md:px-8 md:py-11"><div className="flex flex-col justify-between gap-5 sm:flex-row sm:items-end"><div><p className="text-[10px] font-bold uppercase tracking-[.17em] text-[#438278]">Company workspace · Hiring</p><h1 className="mt-2 text-3xl font-semibold tracking-[-.04em] sm:text-4xl">Your roles</h1><p className="mt-2 text-sm text-[#74817a]">Keep track of each opening, its audience, and applicant activity.</p></div><div className="flex gap-2"><Link href="/company/setup" className="inline-flex h-10 items-center rounded-xl border border-[#d9e2d9] bg-white px-4 text-xs font-semibold text-[#40534a]">Company profile</Link><Link href="/company/jobs/new" className="inline-flex h-10 items-center gap-2 rounded-xl bg-[#173f3a] px-4 text-xs font-semibold text-white">＋ Create role</Link></div></div>
      <section className="mt-7 grid gap-4 sm:grid-cols-3"><Summary label="Total roles" value={jobs.length} detail="All openings and drafts" icon="▤"/><Summary label="Published" value={published} detail="Visible to eligible candidates" icon="↗"/><Summary label="Applicants" value={applicantTotal} detail="Across all your roles" icon="♙"/></section>
      {message && <div className="mt-6 rounded-2xl border border-[#dfe6de] bg-white p-5 text-sm text-[#6c7973]">{message}{message.includes("Sign in") && <Link href="/login" className="ml-2 font-semibold text-[#438278]">Sign in →</Link>}</div>}
      <section className="mt-6 overflow-hidden rounded-2xl border border-[#e4e9e2] bg-white shadow-[0_2px_8px_rgba(27,53,41,.025)]"><div className="flex items-center justify-between border-b border-[#edf0eb] px-5 py-4 md:px-6"><div><h2 className="text-sm font-semibold">Role performance</h2><p className="mt-1 text-xs text-[#88948e]">Candidate volume is updated from submitted applications.</p></div></div>
        {jobs.length ? <div className="divide-y divide-[#edf0eb]">{jobs.map((job) => <article key={job.id} className="flex flex-col gap-4 px-5 py-5 transition hover:bg-[#fcfdfa] md:flex-row md:items-center md:px-6"><span className="grid size-11 shrink-0 place-items-center rounded-xl bg-[#edf5ed] text-sm font-bold text-[#438278]">{job.title.slice(0, 1).toUpperCase()}</span><div className="min-w-0 flex-1"><div className="flex flex-wrap items-center gap-2"><h3 className="truncate text-sm font-semibold text-[#34433e]">{job.title}</h3>{job.target_institute && <span className="rounded-full bg-[#f1f7e0] px-2 py-1 text-[9px] font-bold text-[#6f8437]">{job.target_institute} campus</span>}<span className={`rounded-full px-2 py-1 text-[9px] font-bold ${job.status === "PUBLISHED" ? "bg-[#edf5ed] text-[#438278]" : "bg-[#f3f4f1] text-[#737f77]"}`}>{job.status}</span></div><p className="mt-1.5 text-[11px] text-[#88948e]">{job.department || "General"} <span className="mx-1">·</span> {job.location || "Location flexible"} <span className="mx-1">·</span> {job.employment_type || "Role"}</p></div><div className="flex items-center gap-3 md:gap-5"><div className="min-w-[76px] rounded-xl bg-[#f6f8f4] px-3 py-2 text-center"><p className="text-lg font-semibold tracking-tight text-[#2f493d]">{counts[job.id] ?? "–"}</p><p className="text-[9px] font-medium text-[#849088]">applicants</p></div><Link href={`/company/jobs/${job.id}/candidates`} className="whitespace-nowrap text-xs font-semibold text-[#438278]">Review candidates →</Link></div></article>)}</div> : !message && <div className="px-6 py-14 text-center"><span className="mx-auto grid size-12 place-items-center rounded-2xl bg-[#edf5ed] text-lg text-[#438278]">＋</span><h3 className="mt-4 text-sm font-semibold">Start with your first opening</h3><p className="mt-1 text-xs text-[#829088]">Publish a role publicly or share it with students at a specific institute.</p><Link href="/company/jobs/new" className="mt-4 inline-flex rounded-lg bg-[#173f3a] px-4 py-2.5 text-xs font-semibold text-white">Create a role</Link></div>}
      </section><footer className="py-7 text-center text-[10px] text-[#9aa49e]">© 2026 Candidex · Hiring, made more human.</footer>
    </div></main>;
}

function Summary({ label, value, detail, icon }: { label: string; value: number; detail: string; icon: string }) { return <article className="rounded-2xl border border-[#e4e9e2] bg-white p-5"><div className="flex items-start justify-between"><span className="text-xs font-medium text-[#7a8780]">{label}</span><span className="grid size-9 place-items-center rounded-xl bg-[#eaf4ed] text-sm text-[#468272]">{icon}</span></div><p className="mt-4 text-[31px] font-semibold tracking-[-.05em]">{value}</p><p className="mt-1 text-[10px] text-[#8d9992]">{detail}</p></article>; }
