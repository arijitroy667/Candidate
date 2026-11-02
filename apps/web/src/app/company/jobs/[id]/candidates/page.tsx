"use client";

import Link from "next/link";
import { useParams } from "next/navigation";
import { useCallback, useEffect, useMemo, useState } from "react";
import { api, type Job, type JobCandidate } from "../../../../../lib/api";
import { createClient } from "../../../../../lib/supabase/client";
import WorkspaceHeader from "../../../../../components/workspace-header";

type ScoreWeights = { resume: number; assessment: number; interview: number; communication: number; experience: number; threshold: number };
const DEFAULT_WEIGHTS: ScoreWeights = { resume: 0.3, assessment: 0.25, interview: 0.2, communication: 0.15, experience: 0.1, threshold: 70 };

export default function CandidatesPage() {
  const { id } = useParams<{ id: string }>();
  const [job, setJob] = useState<Job | null>(null);
  const [candidates, setCandidates] = useState<JobCandidate[]>([]);
  const [weights, setWeights] = useState<ScoreWeights>(DEFAULT_WEIGHTS);
  const [message, setMessage] = useState("Loading candidates...");
  const [busy, setBusy] = useState(false);
  const totalWeight = useMemo(() => weights.resume + weights.assessment + weights.interview + weights.communication + weights.experience, [weights]);

  const load = useCallback(async () => {
    const session = (await createClient().auth.getSession()).data.session;
    if (!session) { setMessage("Sign in as a recruiter to view candidates."); return; }
    try {
      const [jobData, items] = await Promise.all([api.job(session.access_token, id), api.jobCandidates(session.access_token, id)]);
      setJob(jobData);
      const config = { ...DEFAULT_WEIGHTS, ...(jobData.scoring_config ?? {}) };
      setWeights({ resume: config.resume, assessment: config.assessment, interview: config.interview, communication: config.communication, experience: config.experience, threshold: config.threshold });
      setCandidates(items);
      setMessage("");
    } catch (error) {
      setMessage(error instanceof Error ? error.message : "Unable to load this job's candidate pipeline.");
    }
  }, [id]);

  useEffect(() => { void load(); }, [load]);

  async function saveScoring() {
    const session = (await createClient().auth.getSession()).data.session;
    if (!session) { setMessage("Sign in as a recruiter to update scoring."); return; }
    if (Math.abs(totalWeight - 1) > 0.00001) { setMessage("Scoring weights must total 100% before saving."); return; }
    setBusy(true);
    try {
      const updated = await api.updateScoring(session.access_token, id, weights);
      setJob(updated as Job);
      setCandidates((items) => items.map((item) => ({ ...item, threshold: weights.threshold, threshold_result: typeof item.score?.final_score === "number" && item.score.final_score >= weights.threshold ? "ABOVE" : item.score ? "BELOW" : "NOT_EVALUATED" })));
      setMessage("Scoring weights and review threshold saved. Recalculate ranking to apply the updated weights.");
    } catch (error) {
      setMessage(error instanceof Error ? error.message : "Unable to save scoring settings.");
    } finally { setBusy(false); }
  }

  async function recalculate() {
    const session = (await createClient().auth.getSession()).data.session;
    if (!session) { setMessage("Sign in as a recruiter to recalculate rankings."); return; }
    setBusy(true);
    setMessage("Reviewing resumes and recalculating the job ranking...");
    try {
      await api.recalculateRankings(session.access_token, id);
      await load();
      setMessage("Ranking refreshed. Scores are recommendations for recruiter review; the system has not made hiring decisions.");
    } catch (error) {
      setMessage(error instanceof Error ? error.message : "Unable to recalculate rankings.");
    } finally { setBusy(false); }
  }

  async function decide(applicationId: string, status: string) {
    const session = (await createClient().auth.getSession()).data.session;
    if (!session) return;
    try {
      await api.updateApplicationStatus(session.access_token, applicationId, status);
      setCandidates((items) => items.map((item) => item.application.id === applicationId ? { ...item, application: { ...item.application, status } } : item));
    } catch (error) { setMessage(error instanceof Error ? error.message : "Unable to update application."); }
  }

  return <main className="min-h-screen bg-[#f5f7f2] px-6 py-8 text-[#1d2725] lg:px-12">
    <div className="mx-auto max-w-7xl">
      <WorkspaceHeader audience="company" />
      <Link href="/company/jobs" className="text-sm text-[#287067]">← Jobs</Link>
      <div className="mt-5 flex flex-wrap items-end justify-between gap-4">
        <div><p className="text-xs font-semibold uppercase tracking-widest text-[#287067]">Recruiter review</p><h1 className="mt-2 text-3xl font-semibold">{job?.title ? `${job.title} candidates` : "Candidate pipeline"}</h1><p className="mt-2 max-w-2xl text-sm text-[#6c7973]">AI-assisted resume screening ranks applicants against this role's requirements. Scores support review; recruiters make every hiring decision.</p></div>
        <button disabled={busy || candidates.length === 0} onClick={() => void recalculate()} className="rounded-lg bg-[#173f3a] px-4 py-2.5 text-sm font-semibold text-white disabled:opacity-50">{busy ? "Working…" : "Recalculate ranking"}</button>
      </div>

      <section className="mt-7 rounded-2xl border border-[#dfe6de] bg-white p-5 sm:p-6">
        <div className="flex flex-wrap items-start justify-between gap-4"><div><p className="text-xs font-semibold uppercase tracking-wider text-[#287067]">Job scoring</p><h2 className="mt-1 text-xl font-semibold">Weights and review threshold</h2><p className="mt-1 text-sm text-[#6c7973]">Above-threshold is a recommendation only; it does not shortlist or reject anyone.</p></div><span className={`rounded-full px-3 py-1 text-xs font-semibold ${Math.abs(totalWeight - 1) < 0.00001 ? "bg-[#e7f0e6] text-[#287067]" : "bg-amber-100 text-amber-800"}`}>Weights {Math.round(totalWeight * 100)}%</span></div>
        <div className="mt-5 grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
          <WeightInput label="Resume fit" value={weights.resume} onChange={(value) => setWeights((current) => ({ ...current, resume: value }))} />
          <WeightInput label="Assessment" value={weights.assessment} onChange={(value) => setWeights((current) => ({ ...current, assessment: value }))} />
          <WeightInput label="Interview" value={weights.interview} onChange={(value) => setWeights((current) => ({ ...current, interview: value }))} />
          <WeightInput label="Communication" value={weights.communication} onChange={(value) => setWeights((current) => ({ ...current, communication: value }))} />
          <WeightInput label="Experience" value={weights.experience} onChange={(value) => setWeights((current) => ({ ...current, experience: value }))} />
          <label className="block text-sm font-medium">Review threshold<input type="number" min="0" max="100" step="1" value={weights.threshold} onChange={(event) => setWeights((current) => ({ ...current, threshold: Number(event.target.value) }))} className="mt-2 h-11 w-full rounded-lg border border-[#dfe6de] bg-white px-3" /><span className="mt-1 block text-xs font-normal text-[#6c7973]">Final score from 0 to 100</span></label>
        </div>
        <div className="mt-5 flex flex-wrap items-center gap-3"><button disabled={busy || Math.abs(totalWeight - 1) > 0.00001 || weights.threshold < 0 || weights.threshold > 100} onClick={() => void saveScoring()} className="rounded-lg border border-[#bfcfc2] px-4 py-2.5 text-sm font-semibold text-[#287067] disabled:opacity-50">Save scoring settings</button><span className="text-xs text-[#6c7973]">Final score uses the weighted components above. Missing assessments/interviews contribute 0 until evaluated.</span></div>
      </section>

      {message && <p role="status" className="mt-5 rounded-xl border border-[#dfe6de] bg-white p-4 text-sm text-[#51645b]">{message}</p>}
      <section className="mt-7 overflow-hidden rounded-2xl border border-[#dfe6de] bg-white">
        <div className="flex flex-wrap items-center justify-between gap-2 border-b border-[#e7ece5] px-5 py-4"><div><h2 className="font-semibold">Ranked applicants</h2><p className="mt-1 text-xs text-[#6c7973]">Rank prioritizes eligibility, then weighted score, confidence, assessment score, and a stable tie-break.</p></div><span className="text-xs text-[#6c7973]">{candidates.length} candidate{candidates.length === 1 ? "" : "s"}</span></div>
        <div className="overflow-x-auto"><table className="w-full min-w-[980px] text-left text-sm">
          <thead className="border-b border-[#e7ece5] bg-[#fafbf8] text-[11px] uppercase tracking-wider text-[#82908a]"><tr><th className="px-4 py-3">Rank</th><th className="px-4 py-3">Candidate</th><th className="px-4 py-3">Eligibility</th><th className="px-4 py-3">Final score</th><th className="px-4 py-3">Threshold</th><th className="px-4 py-3">Confidence</th><th className="px-4 py-3">Human review</th></tr></thead>
          <tbody>{candidates.map((item) => <CandidateRow key={item.application.id} item={item} threshold={weights.threshold} onDecision={decide} />)}</tbody>
        </table></div>
        {!message && candidates.length === 0 && <p className="p-10 text-center text-sm text-[#6c7973]">No applications yet. Applicants will appear here after applying to this job.</p>}
      </section>
    </div>
  </main>;
}

function WeightInput({ label, value, onChange }: { label: string; value: number; onChange: (value: number) => void }) {
  return <label className="block text-sm font-medium">{label}<div className="mt-2 flex h-11 items-center rounded-lg border border-[#dfe6de] px-3"><input aria-label={`${label} weight`} type="number" min="0" max="100" step="1" value={Math.round(value * 100)} onChange={(event) => onChange(Number(event.target.value) / 100)} className="w-full outline-none" /><span className="text-xs text-[#82908a]">%</span></div></label>;
}

function CandidateRow({ item, threshold, onDecision }: { item: JobCandidate; threshold: number; onDecision: (applicationId: string, status: string) => Promise<void> }) {
  const score = item.score;
  const breakdown = score?.score_breakdown ?? {};
  const resume = (breakdown.resume_assessment ?? {}) as Record<string, unknown>;
  const evidence = Array.isArray(resume.evidence) ? resume.evidence as Array<Record<string, unknown>> : [];
  const summaryEvidence = Array.isArray(resume.summary_evidence) ? resume.summary_evidence as string[] : [];
  const gaps = Array.isArray(resume.gaps) ? resume.gaps as string[] : [];
  const scoreValue = typeof score?.final_score === "number" ? score.final_score : null;
  const above = scoreValue !== null && scoreValue >= threshold;
  const eligibility = (breakdown.eligibility ?? {}) as Record<string, unknown>;
  const eligibilityChecks = Array.isArray(eligibility.checks) ? eligibility.checks as Array<Record<string, unknown>> : [];
  const dimensions = (resume.score_dimensions ?? {}) as Record<string, number>;
  const components = (breakdown.components ?? {}) as Record<string, number>;
  const method = resume.method === "LLM" ? `LLM review · ${String(resume.model ?? "configured model")}` : resume.method === "DETERMINISTIC_FALLBACK" ? "Evidence-based fallback · LLM not configured/available" : "Not evaluated";
  return <>
    <tr className="border-b border-[#eef1ec] align-top last:border-0">
      <td className="px-4 py-4 font-semibold text-[#287067]">{item.candidate_rank ? `#${item.candidate_rank}` : "—"}</td>
      <td className="px-4 py-4"><p className="font-medium">{item.profile?.headline || "Candidate"}</p><p className="mt-1 max-w-xs truncate text-xs text-[#6c7973]">{item.profile?.skills || "Profile details unavailable"}</p><p className="mt-1 text-[11px] text-[#82908a]">{item.application.status}</p></td>
      <td className="px-4 py-4"><StatusBadge label={String(eligibility.status ?? "NOT_EVALUATED").replaceAll("_", " ")} good={eligibility.status === "PASS"} /></td>
      <td className="px-4 py-4 font-semibold">{scoreValue === null ? "—" : `${scoreValue.toFixed(1)}%`}</td>
      <td className="px-4 py-4"><StatusBadge label={scoreValue === null ? "Not evaluated" : above ? `Above ${threshold}%` : `Below ${threshold}%`} good={above} /></td>
      <td className="px-4 py-4">{typeof score?.confidence === "number" ? `${Math.round(score.confidence * 100)}%` : "—"}</td>
      <td className="px-4 py-4"><div className="flex flex-wrap gap-2"><button onClick={() => void onDecision(item.application.id, "SHORTLISTED")} className="rounded-md bg-[#173f3a] px-3 py-2 text-xs font-medium text-white">Shortlist</button><button onClick={() => void onDecision(item.application.id, "ON_HOLD")} className="rounded-md border border-[#bfcfc2] px-3 py-2 text-xs text-[#6c7973]">Hold</button></div></td>
    </tr>
      <tr className="border-b border-[#e8eee7] bg-[#fbfcfa]"><td colSpan={7} className="px-4 pb-4 pt-0"><details><summary className="cursor-pointer text-xs font-semibold text-[#287067]">View score basis, resume evidence, and gaps <span className="ml-2 font-normal text-[#82908a]">{method}</span></summary><div className="mt-4 grid gap-5 md:grid-cols-2"><div><h3 className="text-xs font-semibold uppercase tracking-wide text-[#82908a]">Weighted components</h3><div className="mt-2 grid grid-cols-2 gap-2 text-xs">{Object.entries(components).map(([name, value]) => <p key={name} className="rounded-lg bg-white p-2"><span className="capitalize text-[#6c7973]">{name}</span><strong className="ml-2 text-[#173f3a]">{Number(value).toFixed(1)}</strong></p>)}</div><h3 className="mt-4 text-xs font-semibold uppercase tracking-wide text-[#82908a]">Resume fit dimensions</h3><div className="mt-2 grid grid-cols-2 gap-2 text-xs">{Object.entries(dimensions).map(([name, value]) => <p key={name} className="rounded-lg bg-white p-2"><span className="text-[#6c7973]">{name.replaceAll("_", " ")}</span><strong className="ml-2 text-[#173f3a]">{Number(value).toFixed(0)}</strong></p>)}</div>{summaryEvidence.length > 0 && <ul className="mt-3 list-disc space-y-1 pl-5 text-xs text-[#6c7973]">{summaryEvidence.map((signal, index) => <li key={`${signal}-${index}`}>{signal}</li>)}</ul>}<p className="mt-3 text-xs text-[#82908a]">Confidence indicates evidence completeness, not candidate quality.</p></div><div><h3 className="text-xs font-semibold uppercase tracking-wide text-[#82908a]">Resume evidence</h3>{evidence.length ? <ul className="mt-2 space-y-2">{evidence.map((entry, index) => <li key={`${String(entry.quote)}-${index}`} className="rounded-lg bg-white p-3 text-xs"><span className="font-semibold text-[#287067]">{String(entry.criterion)}</span><blockquote className="mt-1 text-[#4c5d55]">“{String(entry.quote)}”</blockquote></li>)}</ul> : <p className="mt-2 rounded-lg bg-white p-3 text-xs text-[#6c7973]">No verbatim resume evidence was available. Review the resume manually.</p>}{gaps.length > 0 && <><h3 className="mt-4 text-xs font-semibold uppercase tracking-wide text-[#82908a]">Gaps for review</h3><ul className="mt-2 list-disc space-y-1 pl-5 text-xs text-[#6c7973]">{gaps.map((gap, index) => <li key={`${gap}-${index}`}>{gap}</li>)}</ul></>}{eligibilityChecks.length > 0 && <><h3 className="mt-4 text-xs font-semibold uppercase tracking-wide text-[#82908a]">Hard eligibility checks</h3><ul className="mt-2 space-y-2">{eligibilityChecks.map((check, index) => <li key={`${String(check.requirement)}-${index}`} className="flex items-center justify-between gap-3 rounded-lg bg-white p-3 text-xs"><span className="text-[#4c5d55]">{String(check.requirement)}</span><StatusBadge label={check.passed ? "Met" : "Not met"} good={check.passed === true} /></li>)}</ul></>}</div></div><p className="mt-4 rounded-lg bg-amber-50 p-3 text-xs text-amber-900">AI output is advisory. Verify evidence and make the hiring decision yourself; threshold status never automatically rejects or advances a candidate.</p></details></td></tr>
  </>;
}

function StatusBadge({ label, good }: { label: string; good: boolean }) {
  return <span className={`inline-block rounded-full px-2.5 py-1 text-[11px] font-semibold ${good ? "bg-[#e7f0e6] text-[#287067]" : "bg-amber-100 text-amber-800"}`}>{label}</span>;
}
