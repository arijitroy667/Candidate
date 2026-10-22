"use client";

import Link from "next/link";
import { useCallback, useEffect, useMemo, useState, type ReactNode } from "react";
import { api, type Application, type Job, type JobCandidate } from "../lib/api";
import { createClient } from "../lib/supabase/client";
import { AccountActions } from "../components/account-actions";

type Notice = { id: string; title: string; body: string; created_at: string; is_read?: boolean; payload?: Record<string, string> };
type CandidateRow = JobCandidate & { job: Job };

const statuses = ["APPLIED", "ELIGIBILITY_CHECK", "RESUME_SCREENING", "ASSESSMENT", "AI_INTERVIEW", "HUMAN_REVIEW", "SHORTLISTED", "ON_HOLD", "REJECTED", "HIRED"];

export default function Home() {
  const [jobs, setJobs] = useState<Job[]>([]);
  const [rows, setRows] = useState<CandidateRow[]>([]);
  const [notices, setNotices] = useState<Notice[]>([]);
  const [applications, setApplications] = useState<Application[]>([]);
  const [role, setRole] = useState<string | null>(null);
  const [accessToken, setAccessToken] = useState("");
  const [email, setEmail] = useState("");
  const [name, setName] = useState("there");
  const [query, setQuery] = useState("");
  const [filter, setFilter] = useState("All candidates");
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [working, setWorking] = useState(false);
  const [selectedCandidates, setSelectedCandidates] = useState<string[]>([]);
  const [comparison, setComparison] = useState<Record<string, unknown>[] | null>(null);

  const load = useCallback(async () => {
    setLoading(true); setError("");
    try {
      const { data } = await createClient().auth.getSession();
      const session = data.session;
      if (!session) { setRole(null); setAccessToken(""); setLoading(false); return; }
      setAccessToken(session.access_token);
      setEmail(session.user.email?.toLowerCase() ?? "");
      const userRole = session.user.user_metadata?.role ?? "CANDIDATE";
      setRole(userRole);
      setName((session.user.user_metadata?.full_name as string | undefined)?.split(" ")[0] || session.user.email?.split("@")[0] || "there");
      if (userRole === "CANDIDATE") {
        const items = await api.applications(session.access_token);
        setApplications(items);
        return;
      }
      const [jobItems, noticeItems] = await Promise.all([
        api.companyJobs(session.access_token),
        api.notifications(session.access_token).catch(() => []),
      ]);
      setJobs(jobItems);
      setNotices(noticeItems as Notice[]);
      const candidateLists = await Promise.all(jobItems.map(async (job) => {
        try { return (await api.jobCandidates(session.access_token, job.id)).map((candidate) => ({ ...candidate, job })); }
        catch { return []; }
      }));
      setRows(candidateLists.flat().sort((a, b) => new Date(b.application.created_at).getTime() - new Date(a.application.created_at).getTime()));
    } catch (reason) { setError(reason instanceof Error ? reason.message : "Unable to load your workspace."); }
    finally { setLoading(false); }
  }, []);

  useEffect(() => { void load(); }, [load]);

  const filteredRows = useMemo(() => rows.filter((row) => {
    const matchesQuery = `${row.profile?.headline ?? ""} ${row.profile?.skills ?? ""} ${row.job.title}`.toLowerCase().includes(query.toLowerCase());
    const matchesStatus = filter === "All candidates" || row.application.status === filter;
    return matchesQuery && matchesStatus;
  }), [rows, query, filter]);
  const activeJobs = jobs.filter((job) => job.status === "PUBLISHED");
  const shortlisted = rows.filter((row) => row.application.status === "SHORTLISTED").length;
  const needsReview = rows.filter((row) => ["APPLIED", "HUMAN_REVIEW", "ON_HOLD"].includes(row.application.status)).length;

  async function refreshRankings(jobId?: string) {
    setWorking(true);
    try {
      const { data } = await createClient().auth.getSession();
      if (!data.session) return;
      const targets = jobId ? jobs.filter((job) => job.id === jobId) : activeJobs;
      await Promise.all(targets.map((job) => api.recalculateRankings(data.session!.access_token, job.id)));
      await load();
    } catch (reason) { setError(reason instanceof Error ? reason.message : "Rankings could not be refreshed."); }
    finally { setWorking(false); }
  }

  async function compareSelected() {
    if (selectedCandidates.length < 2) return;
    const selectedRows = rows.filter((row) => selectedCandidates.includes(row.application.id));
    if (selectedRows.some((row) => row.job.id !== selectedRows[0].job.id)) {
      setError("Choose candidates for the same role to compare their scores fairly."); return;
    }
    const { data } = await createClient().auth.getSession();
    if (!data.session) return;
    try { setComparison(await api.compareCandidates(data.session.access_token, selectedRows[0].job.id, selectedCandidates)); }
    catch (reason) { setError(reason instanceof Error ? reason.message : "Candidate comparison failed."); }
  }

  if (role === "CANDIDATE") return <CandidateHome name={name} email={email} accessToken={accessToken} applications={applications} loading={loading} error={error} onRefresh={load} />;

  return (
    <div className="min-h-screen bg-[#f5f7f2] text-[#1d2725]">
      <aside className="fixed inset-y-0 left-0 z-20 hidden w-[248px] flex-col bg-[#173f3a] px-5 py-6 text-white lg:flex">
        <Link href="/" className="flex items-center gap-3 px-2"><span className="grid size-10 place-items-center rounded-[14px] bg-[#d8f36b] text-sm font-black text-[#173f3a]">cx</span><span className="text-[19px] font-semibold tracking-[-.04em]">candidex</span></Link>
        <div className="mt-12 px-3 text-[10px] font-bold uppercase tracking-[.18em] text-[#91ada0]">Workspace</div>
        <nav className="mt-3 space-y-1 text-sm">
          <SideLink href="#overview" icon="◫" active>Overview</SideLink>
          <SideLink href="/company/jobs" icon="▤">Jobs <span className="ml-auto rounded-full bg-white/10 px-2 py-0.5 text-[10px]">{jobs.length}</span></SideLink>
          <SideLink href="#candidates" icon="♙">Candidates <span className="ml-auto rounded-full bg-white/10 px-2 py-0.5 text-[10px]">{rows.length}</span></SideLink>
          <SideLink href="#activity" icon="◷">Activity history</SideLink>
        </nav>
        <div className="mt-9 px-3 text-[10px] font-bold uppercase tracking-[.18em] text-[#91ada0]">Manage</div>
        <nav className="mt-3 space-y-1 text-sm">
          <SideLink href="/company/jobs/new" icon="＋">Create a role</SideLink>
          <SideLink href="/company/setup" icon="⚙">Company profile</SideLink>
        </nav>
        <div className="mt-auto rounded-2xl border border-white/10 bg-white/[.06] p-4">
          <div className="flex items-center gap-2"><span className="size-2 rounded-full bg-[#d8f36b]"/><span className="text-xs font-semibold">Human-led hiring</span></div>
          <p className="mt-2 text-[11px] leading-5 text-[#abc0b6]">AI brings evidence forward. Your team makes every final decision.</p>
        </div>
        <div className="mt-4 flex items-center gap-3 rounded-xl px-2 py-2"><span className="grid size-9 place-items-center rounded-full bg-[#315b54] text-xs font-semibold text-[#d8f36b]">{name.slice(0, 1).toUpperCase()}</span><div className="min-w-0"><p className="truncate text-xs font-semibold">{name}</p><p className="mt-0.5 text-[10px] text-[#91ada0]">Recruiter workspace</p></div><span className="ml-auto text-[#91ada0]">···</span></div>
      </aside>

      <main className="lg:pl-[248px]">
        <header className="sticky top-0 z-10 border-b border-[#e6ebe4] bg-[#f8faf6]/90 px-5 backdrop-blur-xl md:px-8 xl:px-10">
          <div className="mx-auto flex h-[72px] max-w-[1480px] items-center justify-between gap-4">
            <div className="flex items-center gap-3 lg:hidden"><span className="grid size-9 place-items-center rounded-xl bg-[#173f3a] text-xs font-black text-[#d8f36b]">cx</span><span className="font-semibold">candidex</span></div>
            <div className="hidden items-center gap-2 text-xs text-[#81908a] lg:flex"><span>Workspace</span><span>/</span><span className="font-semibold text-[#34433e]">Overview</span></div>
            <label className="hidden h-10 w-full max-w-[360px] items-center gap-2.5 rounded-xl border border-[#e4e9e2] bg-white px-3.5 text-[#8b9791] md:flex"><span>⌕</span><input value={query} onChange={(event) => setQuery(event.target.value)} className="w-full bg-transparent text-xs text-[#23312d] outline-none placeholder:text-[#9da8a2]" placeholder="Search candidates or roles"/><kbd className="rounded border border-[#edf0eb] px-1.5 py-0.5 text-[9px]">⌘ K</kbd></label>
            <div className="flex items-center gap-2"><button onClick={() => void load()} aria-label="Refresh" className="grid size-10 place-items-center rounded-xl border border-[#e4e9e2] bg-white text-[#53625b] transition hover:bg-[#f1f5ee]">↻</button><button aria-label="Notifications" onClick={() => document.getElementById("activity")?.scrollIntoView({ behavior: "smooth" })} className="relative grid size-10 place-items-center rounded-xl border border-[#e4e9e2] bg-white text-[#53625b]">♧{notices.some((item) => !item.is_read) && <i className="absolute right-2 top-2 size-2 rounded-full bg-[#f0825c]"/>}</button><AccountActions/></div>
          </div>
        </header>

        <div id="overview" className="mx-auto max-w-[1480px] px-5 py-8 md:px-8 md:py-9 xl:px-10">
          <div className="flex flex-col justify-between gap-5 sm:flex-row sm:items-end">
            <div><p className="text-[11px] font-bold uppercase tracking-[.17em] text-[#438278]">Hiring overview <span className="mx-1.5 text-[#b8c2ba]">·</span> Recruiter workspace</p><h1 className="mt-2.5 text-[30px] font-semibold tracking-[-.045em] sm:text-[36px]">Good morning, {name} <span className="text-[#a2b1a8]">✳</span></h1><p className="mt-2 text-sm text-[#74817a]">Here’s what’s happening across your hiring pipeline.</p></div>
            <div className="flex gap-2.5"><button onClick={() => void refreshRankings()} disabled={working || loading} className="inline-flex h-11 items-center gap-2 rounded-xl border border-[#d9e2d9] bg-white px-4 text-xs font-semibold text-[#40534a] transition hover:border-[#aebfb0] disabled:opacity-50"><span>{working ? "◌" : "↻"}</span>{working ? "Refreshing…" : "Refresh rankings"}</button><Link href="/company/jobs/new" className="inline-flex h-11 items-center gap-2 rounded-xl bg-[#173f3a] px-4 text-xs font-semibold text-white shadow-sm transition hover:bg-[#22574e]"><span className="text-base leading-none">＋</span>Create new role</Link></div>
          </div>

          {error && <div className="mt-6 flex items-center justify-between rounded-xl border border-[#f2c8b9] bg-[#fff8f5] px-4 py-3 text-sm text-[#9a4a30]"><span>{error}</span><div className="flex items-center gap-3"><button onClick={() => void load()} className="font-semibold">Try again</button>{role === "COMPANY_ADMIN" && <Link href="/company/setup" className="font-semibold underline">Set up company</Link>}</div></div>}
          {!role && !loading && <div className="mt-8 rounded-2xl border border-[#e1e9df] bg-white p-8"><h2 className="text-lg font-semibold">Welcome to Candidex</h2><p className="mt-2 text-sm text-[#74817a]">Sign in to see your hiring workspace and application history.</p><div className="mt-5 flex gap-3"><Link href="/login" className="rounded-lg bg-[#173f3a] px-4 py-2.5 text-sm font-semibold text-white">Sign in</Link><Link href="/register" className="rounded-lg border border-[#dfe6de] px-4 py-2.5 text-sm font-semibold text-[#40534a]">Create account</Link></div></div>}

          {role && role !== "CANDIDATE" && <>
            <section className="mt-8 grid gap-4 sm:grid-cols-2 xl:grid-cols-4">
              <MetricCard label="Active roles" value={activeJobs.length} detail={`${jobs.filter((job) => job.status === "DRAFT").length} drafts in progress`} icon="▤" tint="mint" trend="Open roles" loading={loading}/>
              <MetricCard label="Total applicants" value={rows.length} detail={`${rows.filter((row) => new Date(row.application.created_at).toDateString() === new Date().toDateString()).length} received today`} icon="♙" tint="lavender" trend="Across all roles" loading={loading}/>
              <MetricCard label="Need your review" value={needsReview} detail="Applications ready for a decision" icon="◷" tint="amber" trend="Review queue" loading={loading}/>
              <MetricCard label="Shortlisted" value={shortlisted} detail="Human-approved candidates" icon="✳" tint="blue" trend="Across all roles" loading={loading}/>
            </section>

            <section className="mt-6 grid gap-5 xl:grid-cols-[minmax(0,1.55fr)_minmax(320px,.85fr)]">
              <div className="rounded-2xl border border-[#e4e9e2] bg-white p-5 md:p-6">
                <div className="flex flex-wrap items-start justify-between gap-3"><div><h2 className="text-[15px] font-semibold tracking-tight">Hiring pipeline</h2><p className="mt-1 text-xs text-[#88948e]">Candidate distribution by current stage</p></div><span className="rounded-lg bg-[#f5f7f2] px-3 py-2 text-[10px] font-semibold text-[#68776e]">All active roles⌄</span></div>
                <div className="mt-7 space-y-[17px]">{["Applied", "Screening", "Assessment", "AI interview", "Human review", "Shortlisted"].map((stage, index) => {
                  const count = stageCount(rows, index); const max = Math.max(rows.length, 1); const width = Math.max(count ? count / max * 100 : 0, count ? 7 : 0);
                  return <div key={stage} className="grid grid-cols-[96px_1fr_30px] items-center gap-3 text-xs"><span className="text-[#64736b]">{stage}</span><div className="h-[9px] overflow-hidden rounded-full bg-[#f0f3ee]"><div className={`h-full rounded-full transition-all ${["bg-[#76b6a7]", "bg-[#76b6a7]", "bg-[#9c9bdd]", "bg-[#7fa9d1]", "bg-[#e4b86d]", "bg-[#76a47a]"][index]}`} style={{ width: `${width}%` }}/></div><span className="text-right font-semibold text-[#36453e]">{loading ? "–" : count}</span></div>;
                })}</div>
                <div className="mt-7 flex flex-wrap items-center gap-x-5 gap-y-2 border-t border-[#edf0eb] pt-4 text-[10px] text-[#849088]"><span><i className="mr-1.5 inline-block size-2 rounded-full bg-[#76b6a7]"/>Early stages</span><span><i className="mr-1.5 inline-block size-2 rounded-full bg-[#9c9bdd]"/>Assessment</span><span><i className="mr-1.5 inline-block size-2 rounded-full bg-[#e4b86d]"/>Human attention</span><span className="ml-auto">{rows.length} applicants total</span></div>
              </div>

              <div className="rounded-2xl border border-[#e4e9e2] bg-white p-5 md:p-6">
                <div className="flex items-start justify-between"><div><h2 className="text-[15px] font-semibold tracking-tight">Roles at a glance</h2><p className="mt-1 text-xs text-[#88948e]">Applicant activity by role</p></div><Link href="/company/jobs" className="text-xs font-semibold text-[#438278]">All roles →</Link></div>
                <div className="mt-3 divide-y divide-[#edf0eb]">{jobs.slice(0, 4).map((job) => {
                  const count = rows.filter((row) => row.job.id === job.id).length;
                  return <Link key={job.id} href={`/company/jobs/${job.id}/candidates`} className="flex items-center gap-3 py-3.5 transition hover:bg-[#fbfcfa]"><span className="grid size-9 shrink-0 place-items-center rounded-xl bg-[#eff5ef] text-sm font-semibold text-[#438278]">{job.title.slice(0, 1).toUpperCase()}</span><span className="min-w-0 flex-1"><span className="block truncate text-xs font-semibold text-[#34433e]">{job.title}</span><span className="mt-1 block text-[10px] text-[#89958e]">{job.location || "Location flexible"} · {job.status.toLowerCase()}</span></span><span className="text-right"><span className="block text-sm font-semibold text-[#34433e]">{count}</span><span className="text-[9px] text-[#89958e]">applicants</span></span></Link>;
                })}{!loading && jobs.length === 0 && <EmptyLine text="Create your first role to start building a pipeline."/>}</div>
                <Link href="/company/jobs/new" className="mt-3 flex h-10 items-center justify-center gap-2 rounded-xl border border-dashed border-[#ccd8ce] text-xs font-semibold text-[#438278] transition hover:bg-[#f7faf6]">＋ Add a role</Link>
              </div>
            </section>

            <section id="candidates" className="mt-6 overflow-hidden rounded-2xl border border-[#e4e9e2] bg-white">
              <div className="flex flex-col gap-3 border-b border-[#edf0eb] bg-[#fbfcfa] px-5 py-3 sm:flex-row sm:items-center sm:justify-between md:px-6"><p className="text-[11px] text-[#7c8982]">Select up to 10 applicants for a side-by-side score comparison.</p><button onClick={() => void compareSelected()} disabled={selectedCandidates.length < 2} className="h-8 rounded-lg border border-[#d5e0d7] bg-white px-3 text-[11px] font-semibold text-[#438278] disabled:cursor-not-allowed disabled:opacity-40">Compare selected{selectedCandidates.length ? ` (${selectedCandidates.length})` : ""}</button></div>
              <div className="overflow-x-auto"><table className="w-full min-w-[850px] text-left"><thead className="bg-[#fafbf9] text-[9px] font-bold uppercase tracking-[.12em] text-[#929e97]"><tr><th className="w-10 px-4 py-3.5"/><th className="px-4 py-3.5">Candidate</th><th className="px-4 py-3.5">Applied for</th><th className="px-4 py-3.5">Applied</th><th className="px-4 py-3.5">AI match</th><th className="px-4 py-3.5">Confidence</th><th className="px-4 py-3.5">Stage</th><th className="px-6 py-3.5 text-right">Review</th></tr></thead><tbody className="divide-y divide-[#f0f2ee]">{filteredRows.slice(0, 10).map((row, index) => <CandidateTableRow key={row.application.id} row={row} index={index} selected={selectedCandidates.includes(row.application.id)} onToggle={() => setSelectedCandidates((current) => current.includes(row.application.id) ? current.filter((id) => id !== row.application.id) : current.length >= 10 ? current : [...current, row.application.id])}/>)}</tbody></table></div>
              {!loading && filteredRows.length === 0 && <div className="px-6 py-10"><EmptyLine text={rows.length ? "No candidates match this search and stage." : "New applications will appear here as candidates apply."}/></div>}
              {filteredRows.length > 10 && <div className="border-t border-[#edf0eb] px-6 py-3.5 text-center"><Link href={`/company/jobs/${filteredRows[0].job.id}/candidates`} className="text-xs font-semibold text-[#438278]">View candidate pipeline →</Link></div>}
            </section>

            <section id="activity" className="mt-6 grid gap-5 lg:grid-cols-[1fr_1fr]">
              <div className="rounded-2xl border border-[#e4e9e2] bg-white p-5 md:p-6"><div className="flex items-start justify-between"><div><h2 className="text-[15px] font-semibold tracking-tight">Recent activity</h2><p className="mt-1 text-xs text-[#88948e]">The latest updates across your workspace</p></div><span className="grid size-8 place-items-center rounded-lg bg-[#f3f7f1] text-[#438278]">◷</span></div><div className="mt-3 divide-y divide-[#edf0eb]">{notices.slice(0, 4).map((notice, index) => <div key={notice.id} className="flex gap-3 py-3.5"><span className={`mt-0.5 grid size-8 shrink-0 place-items-center rounded-full text-xs ${index % 2 ? "bg-[#f0edfb] text-[#7770ad]" : "bg-[#eaf4ed] text-[#438278]"}`}>{notice.title.toLowerCase().includes("application") ? "♙" : "↗"}</span><div className="min-w-0 flex-1"><p className="text-xs font-semibold text-[#394840]">{notice.title}</p><p className="mt-1 line-clamp-2 text-[11px] leading-5 text-[#7e8983]">{notice.body}</p></div><span className="shrink-0 text-[9px] text-[#9aa49e]">{timeAgo(notice.created_at)}</span></div>)}{!loading && notices.length === 0 && <EmptyLine text="Updates to jobs and applications will appear here."/>}</div></div>
              <div className="relative overflow-hidden rounded-2xl bg-[#eaf1e9] p-6 md:p-7"><div className="absolute -right-12 -top-14 size-48 rounded-full border-[28px] border-[#d8e5d8]"/><div className="relative"><span className="grid size-9 place-items-center rounded-xl bg-white text-[#438278] shadow-sm">✳</span><p className="mt-5 text-[10px] font-bold uppercase tracking-[.15em] text-[#548076]">Decision support, with evidence</p><h3 className="mt-2 max-w-sm text-xl font-semibold leading-7 tracking-tight text-[#29423a]">A clearer view of every candidate.</h3><p className="mt-2 max-w-sm text-xs leading-5 text-[#6d7f75]">Review fit scores, confidence, assessment results, and interview evidence before making a decision.</p><Link href={jobs[0] ? `/company/jobs/${jobs[0].id}/candidates` : "/company/jobs"} className="mt-5 inline-flex h-9 items-center rounded-lg bg-[#173f3a] px-3 text-xs font-semibold text-white">Open candidate review →</Link></div></div>
            </section>
            <footer className="flex flex-wrap justify-between gap-2 px-1 py-7 text-[10px] text-[#9aa49e]"><span>© 2026 Candidex <span className="mx-1">·</span> Hiring, made more human.</span><span>All candidate decisions remain with your team.</span></footer>
          </>}
        </div>
      </main>
      {comparison && <div className="fixed inset-0 z-40 grid place-items-center bg-[#10221f]/45 p-4" role="dialog" aria-modal="true" aria-label="Candidate comparison"><section className="max-h-[85vh] w-full max-w-3xl overflow-auto rounded-2xl bg-white p-6 shadow-2xl"><div className="flex items-start justify-between"><div><p className="text-[10px] font-bold uppercase tracking-[.15em] text-[#438278]">Recruiter review</p><h2 className="mt-1 text-xl font-semibold">Candidate comparison</h2><p className="mt-1 text-xs text-[#819087]">Compare score evidence, confidence, and application status.</p></div><button onClick={() => setComparison(null)} className="grid size-8 place-items-center rounded-lg bg-[#f3f6f1] text-[#59685f]" aria-label="Close comparison">×</button></div><div className="mt-5 overflow-x-auto"><table className="w-full min-w-[560px] text-left text-xs"><thead><tr className="border-b border-[#e9eee8] text-[10px] uppercase tracking-wider text-[#86928b]"><th className="py-3 pr-4">Candidate</th><th className="py-3 pr-4">Fit score</th><th className="py-3 pr-4">Confidence</th><th className="py-3">Status</th></tr></thead><tbody className="divide-y divide-[#edf0eb]">{comparison.map((entry) => { const app = entry.application as Application; const candidate = entry.candidate as { headline?: string } | null; const score = entry.score as Record<string, unknown> | null; return <tr key={app.id}><td className="py-4 pr-4 font-semibold">{candidate?.headline || "Candidate"}</td><td className="py-4 pr-4 font-semibold text-[#438278]">{typeof score?.final_score === "number" ? `${Math.round(score.final_score)}%` : "Not scored"}</td><td className="py-4 pr-4">{typeof score?.confidence === "number" ? `${Math.round(score.confidence * 100)}%` : "—"}</td><td className="py-4">{humanStatus(app.status)}</td></tr>; })}</tbody></table></div><p className="mt-4 rounded-xl bg-[#f4f7f1] p-3 text-[10px] leading-5 text-[#6e7d74]">Scores support consistent review. Use the underlying resume, assessment, and interview evidence before making a human hiring decision.</p></section></div>}
    </div>
  );
}

function CandidateHome({ name, email, accessToken, applications, loading, error, onRefresh }: { name: string; email: string; accessToken: string; applications: Application[]; loading: boolean; error: string; onRefresh: () => void }) {
  const [jobs, setJobs] = useState<Record<string, Job>>({});
  const [instituteJobs, setInstituteJobs] = useState<Job[]>([]);
  const [instituteLoading, setInstituteLoading] = useState(true);
  useEffect(() => {
    const ids = [...new Set(applications.map((application) => application.job_id))];
    if (!accessToken) return;
    void Promise.all(ids.map(async (id) => { try { return [id, await api.candidateJob(accessToken, id)] as const; } catch { return null; } })).then((items) => setJobs(Object.fromEntries(items.filter((item): item is readonly [string, Job] => item !== null))));
  }, [applications, accessToken]);
  useEffect(() => {
    let cancelled = false;
    if (!accessToken) { setInstituteLoading(false); return; }
    void api.instituteJobs(accessToken).then((items) => { if (!cancelled) setInstituteJobs(items); }).catch(() => { if (!cancelled) setInstituteJobs([]); }).finally(() => { if (!cancelled) setInstituteLoading(false); });
    return () => { cancelled = true; };
  }, [accessToken]);
  const active = applications.filter((item) => !["REJECTED", "HIRED", "WITHDRAWN"].includes(item.status)).length;
  const inProgress = [...applications].sort((a, b) => new Date(b.created_at).getTime() - new Date(a.created_at).getTime());
  return <div className="min-h-screen bg-[#f5f7f2] text-[#1d2725]"><header className="border-b border-[#e4e9e2] bg-white"><div className="mx-auto flex h-[72px] max-w-6xl items-center justify-between px-5"><Link href="/" className="flex items-center gap-3"><span className="grid size-9 place-items-center rounded-xl bg-[#173f3a] text-xs font-black text-[#d8f36b]">cx</span><span className="font-semibold tracking-tight">candidex</span></Link><nav className="flex items-center gap-2"><Link href="/jobs" className="rounded-lg px-3 py-2 text-xs font-semibold text-[#52635a] hover:bg-[#f3f6f1]">Find jobs</Link><Link href="/candidate/applications" className="rounded-lg px-3 py-2 text-xs font-semibold text-[#52635a] hover:bg-[#f3f6f1]">History</Link><Link href="/candidate/profile" className="rounded-lg px-3 py-2 text-xs font-semibold text-[#52635a] hover:bg-[#f3f6f1]">My profile</Link><button onClick={onRefresh} className="grid size-9 place-items-center rounded-lg border border-[#e3e9e2] text-[#53625b]" aria-label="Refresh applications">↻</button><AccountActions/></nav></div></header><main className="mx-auto max-w-6xl px-5 py-9"><p className="text-[10px] font-bold uppercase tracking-[.16em] text-[#438278]">Candidate workspace <span className="mx-1.5 text-[#b8c2ba]">·</span> Your journey</p><div className="mt-2 flex flex-col justify-between gap-4 sm:flex-row sm:items-end"><div><h1 className="text-3xl font-semibold tracking-[-.04em]">Welcome back, {name}</h1><p className="mt-2 text-sm text-[#74817a]">Keep track of your opportunities and what comes next.</p></div><div className="flex flex-wrap gap-2"><Link href="/jobs" className="inline-flex h-10 items-center justify-center gap-2 rounded-xl border border-[#d9e2d9] bg-white px-4 text-xs font-semibold text-[#40534a]">Explore open roles <span>↗</span></Link><Link href="/jobs?board=institute" className="inline-flex h-10 items-center justify-center gap-2 rounded-xl bg-[#173f3a] px-4 text-xs font-semibold text-white">My institute jobs <span>✳</span></Link></div></div>{error && <p className="mt-6 rounded-xl border border-[#f2c8b9] bg-[#fff8f5] p-4 text-sm text-[#9a4a30]">{error}</p>}<section className="mt-7 grid gap-4 sm:grid-cols-3"><MetricCard label="Applications sent" value={applications.length} detail="Your complete application history" icon="▤" tint="mint" trend="All time" loading={loading}/><MetricCard label="In progress" value={active} detail="Applications currently moving forward" icon="◷" tint="lavender" trend="Active" loading={loading}/><MetricCard label="Shortlisted" value={applications.filter((item) => item.status === "SHORTLISTED").length} detail="Roles where you advanced" icon="✳" tint="blue" trend="Across all roles" loading={loading}/></section><section className="mt-6 overflow-hidden rounded-2xl border border-[#dce7d9] bg-white shadow-[0_2px_8px_rgba(27,53,41,.025)]"><div className="flex flex-wrap items-center justify-between gap-3 border-b border-[#edf0eb] px-5 py-4 md:px-6"><div><p className="text-[10px] font-bold uppercase tracking-[.14em] text-[#438278]">Matched to your sign-in email</p><h2 className="mt-1 text-[15px] font-semibold">Opportunities at your institute</h2><p className="mt-1 text-xs text-[#88948e]">Roles shared with candidates using @{email.split("@")[1] || "your institute email"}</p></div><Link href="/jobs?board=institute" className="text-xs font-semibold text-[#438278]">View institute jobs →</Link></div>{instituteLoading ? <div className="grid gap-3 p-5 sm:grid-cols-2 lg:grid-cols-3">{[1, 2, 3].map((item) => <div key={item} className="h-24 animate-pulse rounded-xl bg-[#f4f7f2]"/>)}</div> : instituteJobs.length ? <div className="grid gap-3 p-5 sm:grid-cols-2 lg:grid-cols-3">{instituteJobs.slice(0, 3).map((job) => <Link key={job.id} href={`/jobs/${job.id}`} className="rounded-xl border border-[#e8eee6] p-4 transition hover:border-[#bdcec0] hover:bg-[#fcfdfa]"><span className="text-[9px] font-bold uppercase tracking-[.12em] text-[#6f8437]">{job.target_institute} · campus role</span><h3 className="mt-2 truncate text-sm font-semibold text-[#34433e]">{job.title}</h3><p className="mt-1 truncate text-[10px] text-[#88948e]">{job.location || "Location flexible"} <span className="mx-1">·</span> {job.employment_type || "Role"}</p><span className="mt-3 inline-block text-[10px] font-semibold text-[#438278]">View opportunity ↗</span></Link>)}</div> : <div className="flex flex-col gap-3 px-5 py-5 sm:flex-row sm:items-center sm:justify-between md:px-6"><p className="max-w-xl text-xs leading-5 text-[#7d8982]">No institute-only roles match your email domain yet. Jobs targeted to your institute will show here automatically.</p><Link href="/jobs?board=institute" className="whitespace-nowrap text-xs font-semibold text-[#438278]">Check institute jobs →</Link></div>}</section><section className="mt-6 grid gap-5 lg:grid-cols-[1.5fr_.8fr]"><div className="rounded-2xl border border-[#e4e9e2] bg-white"><div className="flex items-center justify-between border-b border-[#edf0eb] p-5 md:px-6"><div><h2 className="text-[15px] font-semibold">Your applications</h2><p className="mt-1 text-xs text-[#88948e]">Status and history for every role you applied to</p></div><span className="rounded-full bg-[#edf5ed] px-2.5 py-1 text-[10px] font-bold text-[#498073]">{applications.length}</span></div><div className="divide-y divide-[#edf0eb]">{inProgress.map((application) => <article key={application.id} className="flex flex-col gap-4 px-5 py-4 sm:flex-row sm:items-center md:px-6"><span className="grid size-10 shrink-0 place-items-center rounded-xl bg-[#eff5ef] font-semibold text-[#438278]">{(jobs[application.job_id]?.title ?? "J").slice(0, 1).toUpperCase()}</span><div className="min-w-0 flex-1"><h3 className="truncate text-sm font-semibold">{jobs[application.job_id]?.title ?? `Application ${application.id.slice(0, 8)}`}</h3><p className="mt-1 text-[11px] text-[#88948e]">{jobs[application.job_id]?.location || "Role"} <span className="mx-1">·</span> Applied {new Date(application.created_at).toLocaleDateString()}</p></div><span className="self-start rounded-full bg-[#edf5ed] px-3 py-1.5 text-[10px] font-semibold text-[#438278] sm:self-auto">{humanStatus(application.status)}</span><Link href="/candidate/applications" className="text-xs font-semibold text-[#438278]">View history →</Link></article>)}{!loading && applications.length === 0 && <div className="p-10 text-center"><span className="mx-auto grid size-12 place-items-center rounded-2xl bg-[#eff5ef] text-lg text-[#438278]">▤</span><h3 className="mt-4 text-sm font-semibold">Your next opportunity starts here</h3><p className="mx-auto mt-1 max-w-sm text-xs leading-5 text-[#829088]">Explore open roles and apply. Your applications and progress will be saved in this history.</p><Link href="/jobs" className="mt-4 inline-flex rounded-lg bg-[#173f3a] px-4 py-2.5 text-xs font-semibold text-white">Browse jobs</Link></div>}</div></div><div className="rounded-2xl border border-[#e4e9e2] bg-white p-5 md:p-6"><h2 className="text-[15px] font-semibold">Your progress</h2><p className="mt-1 text-xs text-[#88948e]">Typical steps after you apply</p><div className="mt-6 space-y-0">{["Application received", "Resume review", "Assessment", "Text interview", "Recruiter decision"].map((step, index) => <div key={step} className="flex gap-3"><div className="flex flex-col items-center"><span className={`grid size-7 place-items-center rounded-full text-[10px] font-bold ${index === 0 && applications.length ? "bg-[#dff0e5] text-[#3f806f]" : "bg-[#f3f5f1] text-[#9ca79f]"}`}>{index === 0 && applications.length ? "✓" : index + 1}</span>{index < 4 && <span className="h-8 w-px bg-[#e8ede6]"/>}</div><p className={`pt-1.5 text-xs ${index === 0 && applications.length ? "font-semibold text-[#40534a]" : "text-[#89958e]"}`}>{step}</p></div>)}</div><div className="mt-5 rounded-xl bg-[#f4f7f1] p-3.5"><p className="text-[11px] font-semibold text-[#465950]">You’re in control</p><p className="mt-1 text-[10px] leading-4 text-[#839087]">Your application status updates here when the hiring team takes action.</p></div></div></section><footer className="py-7 text-center text-[10px] text-[#9aa49e]">© 2026 Candidex <span className="mx-1">·</span> Hiring, made more human.</footer></main></div>;
}

function CandidateTableRow({ row, index, selected, onToggle }: { row: CandidateRow; index: number; selected: boolean; onToggle: () => void }) {
  const score = typeof row.score?.final_score === "number" ? row.score.final_score : null;
  const confidence = typeof row.score?.confidence === "number" ? row.score.confidence : null;
  const palette = ["bg-[#e5f0ec] text-[#467c6d]", "bg-[#eeeafb] text-[#7770a8]", "bg-[#f9eee4] text-[#ad7750]", "bg-[#e8eff8] text-[#587ca5]"];
  return <tr className="transition hover:bg-[#fcfdfa]"><td className="px-4 py-3.5"><input type="checkbox" aria-label={`Select ${row.profile?.headline || "candidate"} for comparison`} checked={selected} onChange={onToggle} className="size-3.5 accent-[#438278]"/></td><td className="px-4 py-3.5"><div className="flex items-center gap-3"><span className={`grid size-9 shrink-0 place-items-center rounded-full text-xs font-bold ${palette[index % palette.length]}`}>{(row.profile?.headline || "C").slice(0, 1).toUpperCase()}</span><div><p className="max-w-[190px] truncate text-xs font-semibold text-[#34433e]">{row.profile?.headline || "Candidate"}</p><p className="mt-1 max-w-[190px] truncate text-[10px] text-[#929d96]">{row.profile?.skills || "Profile details not provided"}</p></div></div></td><td className="px-4 py-3.5"><Link href={`/company/jobs/${row.job.id}/candidates`} className="max-w-[145px] truncate text-xs font-medium text-[#53635b] hover:text-[#438278]">{row.job.title}</Link></td><td className="px-4 py-3.5 text-[11px] text-[#7e8a83]">{new Date(row.application.created_at).toLocaleDateString(undefined, { month: "short", day: "numeric" })}</td><td className="px-4 py-3.5"><span className={`text-xs font-bold ${score !== null && score >= 75 ? "text-[#438278]" : "text-[#596b61]"}`}>{score === null ? "—" : `${Math.round(score)}%`}</span></td><td className="px-4 py-3.5"><div className="flex items-center gap-2"><span className="h-1.5 w-14 overflow-hidden rounded-full bg-[#edf0eb]"><i className="block h-full rounded-full bg-[#89b49f]" style={{ width: `${Math.min(100, Math.round((confidence ?? 0) * 100))}%` }}/></span><span className="text-[10px] text-[#718078]">{confidence === null ? "—" : `${Math.round(confidence * 100)}%`}</span></div></td><td className="px-4 py-3.5"><span className="whitespace-nowrap rounded-full bg-[#f2f5f0] px-2.5 py-1.5 text-[9px] font-semibold text-[#637269]">{humanStatus(row.application.status)}</span></td><td className="px-6 py-3.5 text-right"><Link href={`/company/jobs/${row.job.id}/candidates`} className="whitespace-nowrap text-[11px] font-semibold text-[#438278]">Review →</Link></td></tr>;
}

function MetricCard({ label, value, detail, icon, tint, trend, loading }: { label: string; value: number; detail: string; icon: string; tint: string; trend: string; loading: boolean }) {
  const tints: Record<string, string> = { mint: "bg-[#eaf4ed] text-[#468272]", lavender: "bg-[#efedfa] text-[#7771a8]", amber: "bg-[#fbf1e2] text-[#b18342]", blue: "bg-[#eaf0f8] text-[#6482a4]" };
  return <article className="rounded-2xl border border-[#e4e9e2] bg-white p-5 transition hover:border-[#c9d6cb]"><div className="flex items-start justify-between"><span className="text-xs font-medium text-[#7a8780]">{label}</span><span className={`grid size-9 place-items-center rounded-xl text-sm ${tints[tint]}`}>{icon}</span></div><div className="mt-4 flex items-baseline gap-2"><span className="text-[31px] font-semibold tracking-[-.05em]">{loading ? "–" : value}</span><span className="text-[10px] font-semibold text-[#92a099]">{trend}</span></div><p className="mt-1 text-[10px] text-[#8d9992]">{detail}</p></article>;
}

function SideLink({ href, icon, active, children }: { href: string; icon: string; active?: boolean; children: ReactNode }) {
  return <Link href={href} className={`flex h-10 items-center gap-3 rounded-xl px-3.5 transition ${active ? "bg-white/[.13] font-semibold text-white" : "text-[#b9cbc2] hover:bg-white/[.07] hover:text-white"}`}><span className="w-4 text-center text-[15px]">{icon}</span>{children}</Link>;
}

function EmptyLine({ text }: { text: string }) { return <p className="py-6 text-center text-xs text-[#87938c]">{text}</p>; }
function humanStatus(status: string) { return status.toLowerCase().replaceAll("_", " ").replace(/\b\w/g, (letter) => letter.toUpperCase()); }
function stageCount(items: CandidateRow[], index: number) {
  const names = [["APPLIED"], ["ELIGIBILITY_CHECK", "RESUME_SCREENING"], ["ASSESSMENT"], ["AI_INTERVIEW"], ["HUMAN_REVIEW", "ON_HOLD"], ["SHORTLISTED"]][index];
  return items.filter((item) => names.includes(item.application.status)).length;
}
function timeAgo(value: string) { const days = Math.floor((Date.now() - new Date(value).getTime()) / 86400000); if (!Number.isFinite(days) || days < 0) return "now"; if (!days) return "today"; if (days === 1) return "1 day"; if (days < 7) return `${days} days`; return new Date(value).toLocaleDateString(undefined, { month: "short", day: "numeric" }); }
