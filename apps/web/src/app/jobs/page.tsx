"use client";

import Link from "next/link";
import { useEffect, useMemo, useState } from "react";
import { api, type Job } from "../../lib/api";
import { createClient } from "../../lib/supabase/client";

type Board = "public" | "institute";

export default function JobsPage() {
  const [jobs, setJobs] = useState<Job[]>([]);
  const [instituteJobs, setInstituteJobs] = useState<Job[]>([]);
  const [board, setBoard] = useState<Board>("public");
  const [email, setEmail] = useState("");
  const [role, setRole] = useState("");
  const [loading, setLoading] = useState(true);
  const [instituteLoading, setInstituteLoading] = useState(false);
  const [error, setError] = useState("");
  const [query, setQuery] = useState("");

  useEffect(() => {
    let cancelled = false;
    if (new URLSearchParams(window.location.search).get("board") === "institute") setBoard("institute");
    async function load() {
      try {
        const [publicJobs, { data }] = await Promise.all([api.publicJobs(), createClient().auth.getSession()]);
        if (cancelled) return;
        setJobs(publicJobs);
        const session = data.session;
        const accountEmail = session?.user.email?.toLowerCase() ?? "";
        const accountRole = String(session?.user.user_metadata?.role ?? "").toUpperCase();
        setEmail(accountEmail);
        setRole(accountRole);
        if (session && accountRole === "CANDIDATE") {
          setInstituteLoading(true);
          try {
            const items = await api.instituteJobs(session.access_token);
            if (!cancelled) setInstituteJobs(items);
          } catch (reason) {
            if (!cancelled) setError(reason instanceof Error ? reason.message : "Institute roles could not be loaded.");
          } finally {
            if (!cancelled) setInstituteLoading(false);
          }
        }
      } catch (reason) {
        if (!cancelled) setError(reason instanceof Error ? reason.message : "Roles could not be loaded.");
      } finally {
        if (!cancelled) setLoading(false);
      }
    }
    void load();
    return () => { cancelled = true; };
  }, []);

  const candidate = role === "CANDIDATE" && email.includes("@");
  const domain = email.split("@")[1] || "your institute email";
  const visibleJobs = useMemo(() => (board === "institute" ? instituteJobs : jobs).filter((job) =>
    `${job.title} ${job.description} ${job.location ?? ""} ${job.skills.join(" ")}`.toLowerCase().includes(query.toLowerCase()),
  ), [board, instituteJobs, jobs, query]);

  return (
    <main className="min-h-screen bg-[#f5f7f2] px-6 py-8 text-[#1d2725] lg:px-12">
      <div className="mx-auto max-w-6xl">
        <header className="flex flex-wrap items-center justify-between gap-4 border-b border-[#dfe6de] pb-5">
          <Link href="/" className="flex items-center gap-3 text-lg font-semibold"><span className="grid size-9 place-items-center rounded-xl bg-[#173f3a] text-sm text-[#d8f36b]">cx</span>Candidex</Link>
          <nav className="flex flex-wrap items-center gap-2 text-sm"><Link href="/candidate/applications" className="rounded-lg px-3 py-2 text-[#287067] hover:bg-white">Applications</Link><Link href="/login" className="rounded-lg border border-[#c3d2c5] bg-white px-3 py-2 font-medium text-[#315d55]">Sign in</Link></nav>
        </header>
        <section className="mt-10 rounded-3xl bg-[#173f3a] p-6 text-white sm:p-9">
          <p className="text-xs font-semibold uppercase tracking-[0.18em] text-[#d8f36b]">Candidate opportunities</p>
          <h1 className="mt-3 text-3xl font-semibold tracking-tight sm:text-4xl">Find work worth doing.</h1>
          <p className="mt-3 max-w-2xl text-sm leading-6 text-[#d5e0da]">Browse public roles or check opportunities shared specifically with students at your institute.</p>
          <div className="mt-6 flex flex-wrap gap-3">
            <button onClick={() => setBoard("public")} className={`rounded-xl px-4 py-3 text-left text-sm font-semibold ${board === "public" ? "bg-white text-[#173f3a]" : "border border-white/25 bg-white/5 text-white"}`}><span className="block">Public jobs</span><span className="mt-1 block text-xs font-normal opacity-75">Open to all candidates</span></button>
            <button onClick={() => setBoard("institute")} className={`rounded-xl px-4 py-3 text-left text-sm font-semibold ${board === "institute" ? "bg-[#d8f36b] text-[#173f3a]" : "border border-white/25 bg-white/5 text-white"}`}><span className="block">My institute jobs ✳</span><span className="mt-1 block text-xs font-normal opacity-75">{candidate ? `Matched to @${domain}` : "Sign in with your institute email"}</span></button>
          </div>
        </section>

        {board === "institute" && !candidate && <section className="mt-5 flex flex-wrap items-center justify-between gap-4 rounded-2xl border border-[#dfe6de] bg-white p-5"><div><h2 className="font-semibold">Institute jobs are available to signed-in candidates</h2><p className="mt-1 text-sm text-[#6c7973]">Sign in using the student email domain your institute uses. Matching roles appear here automatically.</p></div><Link href="/login?role=candidate" className="rounded-lg bg-[#173f3a] px-4 py-2.5 text-sm font-medium text-white">Candidate sign in</Link></section>}
        {board === "institute" && candidate && <p className="mt-5 rounded-xl border border-[#dfe6de] bg-white p-4 text-sm text-[#617168]">Showing published roles targeted to <strong className="text-[#173f3a]">@{domain}</strong>.</p>}
        {error && <p role="status" className="mt-5 rounded-xl border border-red-200 bg-red-50 p-4 text-sm text-red-700">{error}</p>}

        <section className="mt-8">
          <div className="flex flex-col justify-between gap-4 sm:flex-row sm:items-end"><div><p className="text-xs font-semibold uppercase tracking-[0.16em] text-[#287067]">{board === "institute" ? "Institute board" : "Public board"}</p><h2 className="mt-2 text-2xl font-semibold">{board === "institute" ? "Roles for your institute" : "Open roles"}</h2><p className="mt-2 text-sm text-[#6c7973]">{board === "institute" ? "Private campus opportunities matched by student email domain." : "Published roles available to everyone."}</p></div><input value={query} onChange={(event) => setQuery(event.target.value)} className="h-11 rounded-xl border border-[#dfe6de] bg-white px-4 text-sm outline-none focus:border-[#87a52e] sm:w-72" placeholder="Search roles or skills" /></div>
          {loading || (board === "institute" && candidate && instituteLoading) ? <div className="mt-6 h-40 animate-pulse rounded-2xl bg-white" /> : board === "institute" && !candidate ? null : (
            <div className="mt-6 grid gap-4 md:grid-cols-2">
              {visibleJobs.map((job) => <article key={job.id} className="rounded-2xl border border-[#dfe6de] bg-white p-6"><p className="text-xs font-semibold uppercase tracking-wider text-[#287067]">{board === "institute" ? `${job.target_institute} · campus role` : job.location || "Remote"}</p><Link href={`/jobs/${job.id}`} className="mt-2 block text-xl font-semibold hover:text-[#287067]">{job.title}</Link><p className="mt-3 line-clamp-3 text-sm leading-6 text-[#6c7973]">{job.description}</p><div className="mt-5 flex flex-wrap gap-2">{job.skills.map((skill) => <span key={skill} className="rounded-full bg-[#e7f0e6] px-3 py-1 text-xs text-[#287067]">{skill}</span>)}</div><Link href={`/jobs/${job.id}`} className="mt-5 inline-block text-sm font-medium text-[#287067]">View role →</Link></article>)}
              {!visibleJobs.length && <div className="col-span-full rounded-2xl border border-dashed border-[#bfcfc2] bg-white p-10 text-center"><h3 className="font-semibold">{board === "institute" ? "No roles posted for your institute yet" : "No published roles yet"}</h3><p className="mt-2 text-sm text-[#6c7973]">{board === "institute" ? "When a company shares a role with your institute email domain, it will appear here." : "New opportunities will appear here when employers publish them."}</p></div>}
            </div>
          )}
        </section>
      </div>
    </main>
  );
}
