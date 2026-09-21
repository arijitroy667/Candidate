"use client";

import { useEffect, useState } from "react";
import { api, type Job } from "../../lib/api";

export default function JobsPage() {
  const [jobs, setJobs] = useState<Job[]>([]);
  const [error, setError] = useState("");

  useEffect(() => {
    api.publicJobs().then(setJobs).catch((reason: Error) => setError(reason.message));
  }, []);

  return (
    <main className="min-h-screen bg-[#f5f7f2] px-6 py-10 text-[#1d2725] lg:px-20">
      <div className="mx-auto max-w-5xl">
        <p className="text-xs font-semibold uppercase tracking-[0.18em] text-[#82908a]">Open roles</p>
        <h1 className="mt-2 text-4xl font-semibold tracking-tight">Find work worth doing.</h1>
        <p className="mt-3 text-[#6c7973]">Published opportunities from the Candidex workspace.</p>
        {error && <p className="mt-8 rounded-lg bg-red-50 p-4 text-sm text-red-700">{error}</p>}
        <div className="mt-10 grid gap-4 md:grid-cols-2">
          {jobs.map((job) => (
            <article key={job.id} className="rounded-xl border border-[#dfe6de] bg-white p-6">
              <p className="text-xs font-semibold uppercase tracking-wider text-[#287067]">{job.location || "Remote"}</p>
              <h2 className="mt-2 text-xl font-semibold">{job.title}</h2>
              <p className="mt-3 line-clamp-3 text-sm leading-6 text-[#6c7973]">{job.description}</p>
              <div className="mt-5 flex flex-wrap gap-2">
                {job.skills.map((skill) => <span key={skill} className="rounded-full bg-[#e7f0e6] px-3 py-1 text-xs text-[#287067]">{skill}</span>)}
              </div>
            </article>
          ))}
          {!error && jobs.length === 0 && <p className="text-sm text-[#6c7973]">No published roles yet.</p>}
        </div>
      </div>
    </main>
  );
}