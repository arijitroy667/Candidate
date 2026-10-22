"use client";

import Link from "next/link";
import { useEffect, useMemo, useState } from "react";
import { api, type Job } from "../../lib/api";
import { createClient } from "../../lib/supabase/client";
import { AccountActions } from "../../components/account-actions";

type Board = "public" | "institute";

export default function JobsPage() {
  const [jobs, setJobs] = useState<Job[]>([]);
  const [campusJobs, setCampusJobs] = useState<Job[]>([]);
  const [board, setBoard] = useState<Board>("public");
  const [email, setEmail] = useState("");
  const [role, setRole] = useState("");
  const [query, setQuery] = useState("");
  const [loading, setLoading] = useState(true);
  const [campusLoading, setCampusLoading] = useState(false);
  const [error, setError] = useState("");

  useEffect(() => {
    let cancelled = false;
    if (new URLSearchParams(window.location.search).get("board") === "institute") setBoard("institute");
    void Promise.all([
      api.publicJobs(),
      createClient().auth.getSession(),
    ]).then(async ([publicItems, { data }]) => {
      if (cancelled) return;
      const session = data.session;
      const accountEmail = session?.user.email?.toLowerCase() ?? "";
      setJobs(publicItems);
      setEmail(accountEmail);
      setRole(String(session?.user.user_metadata?.role ?? ""));
      if (session && accountEmail.includes("@") && session.user.user_metadata?.role === "CANDIDATE") {
        setCampusLoading(true);
        try {
          const items = await api.instituteJobs(session.access_token);
          if (!cancelled) setCampusJobs(items);
        } catch (reason) {
          if (!cancelled) setError(reason instanceof Error ? reason.message : "Campus roles could not be loaded.");
        } finally {
          if (!cancelled) setCampusLoading(false);
        }
      }
    }).catch((reason: Error) => { if (!cancelled) setError(reason.message); }).finally(() => { if (!cancelled) setLoading(false); });
    return () => { cancelled = true; };
  }, []);

  const visibleJobs = useMemo(() => (board === "institute" ? campusJobs : jobs).filter((job) =>
    `${job.title} ${job.description} ${job.location ?? ""} ${job.skills.join(" ")}`.toLowerCase().includes(query.toLowerCase()),
  ), [board, campusJobs, jobs, query]);
  const canSeeCampus = role === "CANDIDATE" && email.includes("@");
  const instituteDomain = email.split("@")[1] || "your institute email";

  return (
    <main className="min-h-screen bg-[#f5f7f2] text-[#1d2725]">
      <header className="border-b border-[#e5ebe3] bg-white/90 backdrop-blur">
        <div className="mx-auto flex h-[72px] max-w-7xl items-center justify-between px-5 md:px-8">
          <Link href="/" className="flex items-center gap-3"><span className="grid size-9 place-items-center rounded-xl bg-[#173f3a] text-xs font-black text-[#d8f36b]">cx</span><span className="font-semibold tracking-tight">candidex</span></Link>
          <nav className="flex items-center gap-2"><Link href="/candidate/applications" className="rounded-lg px-3 py-2 text-xs font-semibold text-[#52635a] hover:bg-[#f3f6f1]">My applications</Link><Link href="/candidate/profile" className="rounded-lg px-3 py-2 text-xs font-semibold text-[#52635a] hover:bg-[#f3f6f1]">Profile</Link><AccountActions/></nav>
        </div>
      </header>
      <div className="mx-auto max-w-7xl px-5 py-9 md:px-8 md:py-12">
        <section className="relative overflow-hidden rounded-[28px] bg-[#173f3a] px-6 py-8 text-white md:px-10 md:py-11">
          <div className="absolute -right-12 -top-24 size-72 rounded-full border-[38px] border-white/[.06]"/><div className="absolute -bottom-32 right-40 size-64 rounded-full bg-[#d8f36b]/[.07] blur-2xl"/>
          <div className="relative max-w-2xl"><p className="text-[10px] font-bold uppercase tracking-[.2em] text-[#d8f36b]">Career opportunities</p><h1 className="mt-3 text-3xl font-semibold tracking-[-.04em] md:text-[42px]">Find work worth doing.</h1><p className="mt-3 max-w-xl text-sm leading-6 text-[#ccdbd2]">Explore published opportunities and keep your applications, updates, and next steps together.</p></div>
          <div className="relative mt-7 flex flex-col gap-3 sm:flex-row">
            <button onClick={() => setBoard("public")} className={`rounded-xl px-4 py-3 text-left text-xs font-semibold transition ${board === "public" ? "bg-white text-[#173f3a]" : "border border-white/20 bg-white/[.06] text-white hover:bg-white/10"}`}><span className="block">Public opportunities</span><span className={`mt-1 block text-[10px] font-normal ${board === "public" ? "text-[#76867d]" : "text-[#c3d2c9]"}`}>Roles open to all candidates</span></button>
            <button onClick={() => setBoard("institute")} className={`rounded-xl px-4 py-3 text-left text-xs font-semibold transition ${board === "institute" ? "bg-[#d8f36b] text-[#173f3a]" : "border border-white/20 bg-white/[.06] text-white hover:bg-white/10"}`}><span className="block">My institute roles <span className="ml-1 text-[10px]">✳</span></span><span className={`mt-1 block text-[10px] font-normal ${board === "institute" ? "text-[#5d7042]" : "text-[#c3d2c9]"}`}>{canSeeCampus ? `For @${instituteDomain}` : "For verified institute accounts"}</span></button>
          </div>
        </section>

        {board === "institute" && !canSeeCampus && <section className="mt-6 flex flex-col gap-4 rounded-2xl border border-[#dfe7dc] bg-white p-5 sm:flex-row sm:items-center sm:justify-between"><div><p className="font-semibold">Sign in with your institute account</p><p className="mt-1 text-sm text-[#74817a]">Campus opportunities are matched to your signed-in institution email domain.</p></div><Link href="/login" className="inline-flex h-10 shrink-0 items-center justify-center rounded-xl bg-[#173f3a] px-4 text-xs font-semibold text-white">Sign in</Link></section>}
        {error && <p className="mt-5 rounded-xl border border-[#f2c8b9] bg-[#fff8f5] p-4 text-sm text-[#9a4a30]">{error}</p>}
        <section className="mt-7">
          <div className="flex flex-col justify-between gap-4 sm:flex-row sm:items-end"><div><p className="text-[10px] font-bold uppercase tracking-[.16em] text-[#438278]">{board === "institute" ? `${instituteDomain} · Campus hiring` : "Discover"}</p><h2 className="mt-1 text-2xl font-semibold tracking-tight">{board === "institute" ? "Roles for your institute" : "Open roles"}</h2><p className="mt-1 text-sm text-[#7c8982]">{board === "institute" ? "Opportunities shared specifically with students at your institute." : "Published opportunities from the Candidex workspace."}</p></div><label className="flex h-11 w-full items-center gap-2 rounded-xl border border-[#dfe6de] bg-white px-3.5 text-[#89958e] sm:max-w-[320px]"><span>⌕</span><input value={query} onChange={(event) => setQuery(event.target.value)} className="w-full bg-transparent text-sm text-[#34433e] outline-none placeholder:text-[#9da8a2]" placeholder="Search roles or skills"/><span className="text-[10px]">↵</span></label></div>
          <div className="mt-5 flex items-center justify-between border-b border-[#e2e9e1] pb-3 text-xs text-[#7b8880]"><span>{board === "institute" ? campusJobs.length : jobs.length} published roles</span><span>Sorted by newest</span></div>
          {loading || (board === "institute" && campusLoading) ? <div className="mt-5 grid gap-4 md:grid-cols-2 xl:grid-cols-3">{[0, 1, 2].map((item) => <div key={item} className="h-56 animate-pulse rounded-2xl border border-[#e4e9e2] bg-white" />)}</div> : board === "institute" && !canSeeCampus ? null : (
            <div className="mt-5 grid gap-4 md:grid-cols-2 xl:grid-cols-3">
              {visibleJobs.map((job) => <article key={job.id} className="group flex min-h-[260px] flex-col rounded-2xl border border-[#e4e9e2] bg-white p-5 shadow-[0_2px_8px_rgba(27,53,41,.025)] transition hover:-translate-y-0.5 hover:border-[#bfd1c3] hover:shadow-[0_12px_30px_rgba(27,53,41,.08)]"><div className="flex items-start justify-between gap-3"><span className="grid size-11 shrink-0 place-items-center rounded-xl bg-[#edf5ed] text-base font-bold text-[#438278]">{job.title.slice(0, 1).toUpperCase()}</span>{board === "institute" && <span className="rounded-full bg-[#f1f7e0] px-2.5 py-1 text-[9px] font-bold uppercase tracking-wide text-[#6f8437]">{job.target_institute} campus</span>}</div><div className="mt-4"><p className="text-[10px] font-semibold uppercase tracking-[.12em] text-[#438278]">{job.department || "Opportunity"}</p><Link href={`/jobs/${job.id}`} className="mt-1 block text-lg font-semibold leading-6 tracking-tight text-[#25352d] group-hover:text-[#287067]">{job.title}</Link><p className="mt-1.5 text-xs text-[#7c8982]">{job.location || "Location flexible"} <span className="mx-1">·</span> {job.employment_type || "Full-time"}</p></div><p className="mt-3 line-clamp-2 text-xs leading-5 text-[#718078]">{job.description}</p><div className="mt-3 flex flex-wrap gap-1.5">{job.skills.slice(0, 3).map((skill) => <span key={skill} className="rounded-md bg-[#f4f6f2] px-2 py-1 text-[9px] font-medium text-[#617168]">{skill}</span>)}</div><div className="mt-auto flex items-center justify-between pt-5"><span className="text-[10px] text-[#a0aaa3]">Published {new Date(job.created_at ?? Date.now()).toLocaleDateString(undefined, { month: "short", day: "numeric" })}</span><Link href={`/jobs/${job.id}`} className="text-xs font-semibold text-[#438278]">View opportunity <span aria-hidden="true">↗</span></Link></div></article>)}
              {!visibleJobs.length && <div className="col-span-full rounded-2xl border border-dashed border-[#cbd8cd] bg-white/60 px-5 py-14 text-center"><span className="mx-auto grid size-11 place-items-center rounded-xl bg-[#edf5ed] text-lg text-[#438278]">⌕</span><h3 className="mt-3 text-sm font-semibold text-[#35473e]">{query ? "No roles match that search" : board === "institute" ? "No roles posted for your institute yet" : "No published roles yet"}</h3><p className="mt-1 text-xs text-[#87938c]">{query ? "Try another role title, location, or skill." : "New opportunities will appear here when employers publish them."}</p></div>}
            </div>
          )}
        </section>
      </div>
    </main>
  );
}
