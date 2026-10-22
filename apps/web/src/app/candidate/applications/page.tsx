"use client";

import Link from "next/link";
import { useEffect, useMemo, useState } from "react";
import { api, type Application, type Job } from "../../../lib/api";
import { createClient } from "../../../lib/supabase/client";
import { AccountActions } from "../../../components/account-actions";

type ApplicationFilter = "ALL" | "ACTIVE" | "CLOSED";

export default function ApplicationsPage() {
  const [applications, setApplications] = useState<Application[]>([]);
  const [jobs, setJobs] = useState<Record<string, Job>>({});
  const [message, setMessage] = useState("");
  const [loading, setLoading] = useState(true);
  const [filter, setFilter] = useState<ApplicationFilter>("ALL");

  useEffect(() => {
    let cancelled = false;
    void (async () => {
      try {
        const session = (await createClient().auth.getSession()).data.session;
        if (!session) { setMessage("Sign in to view your application history."); return; }
        const items = await api.applications(session.access_token);
        if (cancelled) return;
        setApplications(items);
        const details = await Promise.all(items.map(async (application) => {
          try { return [application.job_id, await api.candidateJob(session.access_token, application.job_id)] as const; }
          catch { return null; }
        }));
        if (!cancelled) setJobs(Object.fromEntries(details.filter((item): item is readonly [string, Job] => item !== null)));
      } catch (error) {
        if (!cancelled) setMessage(error instanceof Error ? error.message : "Your application history could not be loaded.");
      } finally {
        if (!cancelled) setLoading(false);
      }
    })();
    return () => { cancelled = true; };
  }, []);

  const visible = useMemo(() => applications.filter((application) => {
    const isClosed = ["REJECTED", "HIRED", "WITHDRAWN"].includes(application.status);
    return filter === "ALL" || (filter === "CLOSED" ? isClosed : !isClosed);
  }), [applications, filter]);
  const activeCount = applications.filter((item) => !["REJECTED", "HIRED", "WITHDRAWN"].includes(item.status)).length;
  const closedCount = applications.length - activeCount;

  return <main className="min-h-screen bg-[#f5f7f2] text-[#1d2725]">
    <header className="border-b border-[#e5ebe3] bg-white"><div className="mx-auto flex h-[72px] max-w-6xl items-center justify-between px-5 md:px-8"><Link href="/" className="flex items-center gap-3"><span className="grid size-9 place-items-center rounded-xl bg-[#173f3a] text-xs font-black text-[#d8f36b]">cx</span><span className="font-semibold">candidex</span></Link><nav className="flex items-center gap-2"><Link href="/jobs" className="rounded-lg px-3 py-2 text-xs font-semibold text-[#52635a] hover:bg-[#f3f6f1]">Find jobs</Link><Link href="/candidate/profile" className="rounded-lg px-3 py-2 text-xs font-semibold text-[#52635a] hover:bg-[#f3f6f1]">My profile</Link><AccountActions/></nav></div></header>
    <div className="mx-auto max-w-6xl px-5 py-9 md:px-8 md:py-11">
      <Link href="/" className="text-xs font-medium text-[#438278]">← Workspace</Link>
      <div className="mt-5 flex flex-col justify-between gap-5 sm:flex-row sm:items-end"><div><p className="text-[10px] font-bold uppercase tracking-[.17em] text-[#438278]">Candidate workspace · Your journey</p><h1 className="mt-2 text-3xl font-semibold tracking-[-.04em] sm:text-4xl">Application history</h1><p className="mt-2 text-sm text-[#74817a]">Every role you’ve applied for, with the latest status and submission date.</p></div><Link href="/jobs" className="inline-flex h-10 items-center justify-center gap-2 rounded-xl bg-[#173f3a] px-4 text-xs font-semibold text-white">Explore opportunities <span>↗</span></Link></div>
      <section className="mt-7 grid gap-4 sm:grid-cols-3"><SummaryCard label="Applications" value={applications.length} detail="Total submitted" icon="▤"/><SummaryCard label="In progress" value={activeCount} detail="Moving through review" icon="◷"/><SummaryCard label="Completed" value={closedCount} detail="Closed decisions" icon="✓"/></section>
      {message && <div className="mt-6 rounded-2xl border border-[#e2e9e1] bg-white p-5 text-sm text-[#6c7973]">{message}{message.startsWith("Sign in") && <Link href="/login" className="ml-2 font-semibold text-[#438278]">Sign in →</Link>}</div>}
      <section className="mt-6 overflow-hidden rounded-2xl border border-[#e4e9e2] bg-white shadow-[0_2px_8px_rgba(27,53,41,.025)]"><div className="flex flex-col justify-between gap-3 border-b border-[#edf0eb] px-5 py-4 sm:flex-row sm:items-center md:px-6"><div><h2 className="text-sm font-semibold">Your applications</h2><p className="mt-1 text-xs text-[#88948e]">See the role, when you applied, and where it stands</p></div><div className="flex gap-1 rounded-xl bg-[#f3f6f1] p-1">{(["ALL", "ACTIVE", "CLOSED"] as const).map((item) => <button key={item} onClick={() => setFilter(item)} className={`rounded-lg px-3 py-2 text-[10px] font-semibold transition ${filter === item ? "bg-white text-[#27483e] shadow-sm" : "text-[#78867d] hover:text-[#42554a]"}`}>{item === "ALL" ? `All · ${applications.length}` : item === "ACTIVE" ? `In progress · ${activeCount}` : `Completed · ${closedCount}`}</button>)}</div></div>
        {loading ? <div className="space-y-3 p-5">{[1, 2, 3].map((item) => <div key={item} className="h-[86px] animate-pulse rounded-xl bg-[#f5f7f3]"/> )}</div> : visible.length ? <div className="divide-y divide-[#edf0eb]">{visible.map((application) => {
          const job = jobs[application.job_id];
          const closed = ["REJECTED", "HIRED", "WITHDRAWN"].includes(application.status);
          return <article key={application.id} className="flex flex-col gap-4 px-5 py-5 transition hover:bg-[#fcfdfa] sm:flex-row sm:items-center md:px-6"><span className="grid size-11 shrink-0 place-items-center rounded-xl bg-[#edf5ed] text-sm font-bold text-[#438278]">{(job?.title || "J").slice(0, 1).toUpperCase()}</span><div className="min-w-0 flex-1"><div className="flex flex-wrap items-center gap-2"><h3 className="truncate text-sm font-semibold text-[#34433e]">{job?.title ?? `Job ${application.job_id.slice(0, 8)}`}</h3>{job?.target_institute && <span className="rounded-full bg-[#f1f7e0] px-2 py-0.5 text-[9px] font-bold text-[#6f8437]">{job.target_institute} campus</span>}</div><p className="mt-1 text-[11px] text-[#88948e]">{job?.department || job?.location || "Opportunity"}{job?.location && job.department ? ` · ${job.location}` : ""} <span className="mx-1">·</span> Applied {new Date(application.created_at).toLocaleDateString(undefined, { year: "numeric", month: "short", day: "numeric" })}</p><p className="mt-1 text-[10px] text-[#a0aaa3]">Application ref. {application.id.slice(0, 8)}</p></div><div className="flex items-center gap-3 sm:justify-end"><span className={`rounded-full px-3 py-1.5 text-[10px] font-semibold ${closed ? "bg-[#f2f3f1] text-[#707b74]" : "bg-[#edf5ed] text-[#438278]"}`}>{humanStatus(application.status)}</span>{job && <Link href={`/jobs/${job.id}`} className="whitespace-nowrap text-xs font-semibold text-[#438278]">View role →</Link>}</div></article>;
        })}</div> : !message && <div className="px-6 py-14 text-center"><span className="mx-auto grid size-12 place-items-center rounded-2xl bg-[#edf5ed] text-lg text-[#438278]">▤</span><h3 className="mt-4 text-sm font-semibold">{applications.length ? "No applications in this view" : "Your next opportunity starts here"}</h3><p className="mx-auto mt-1 max-w-sm text-xs leading-5 text-[#829088]">{applications.length ? "Choose another filter to see more of your history." : "Browse roles and apply. Your submissions and status updates will be saved here."}</p>{!applications.length && <Link href="/jobs" className="mt-4 inline-flex rounded-lg bg-[#173f3a] px-4 py-2.5 text-xs font-semibold text-white">Browse jobs</Link>}</div>}
      </section>
      <footer className="py-7 text-center text-[10px] text-[#9aa49e]">© 2026 Candidex · Hiring, made more human.</footer>
    </div>
  </main>;
}

function SummaryCard({ label, value, detail, icon }: { label: string; value: number; detail: string; icon: string }) {
  return <article className="rounded-2xl border border-[#e4e9e2] bg-white p-5"><div className="flex items-start justify-between"><span className="text-xs font-medium text-[#7a8780]">{label}</span><span className="grid size-9 place-items-center rounded-xl bg-[#eaf4ed] text-sm text-[#468272]">{icon}</span></div><p className="mt-4 text-[31px] font-semibold tracking-[-.05em]">{value}</p><p className="mt-1 text-[10px] text-[#8d9992]">{detail}</p></article>;
}

function humanStatus(status: string) { return status.toLowerCase().replaceAll("_", " ").replace(/\b\w/g, (letter) => letter.toUpperCase()); }
