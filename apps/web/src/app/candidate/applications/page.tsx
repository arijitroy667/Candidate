"use client";

import { useEffect, useState } from "react";
import { api, type Application } from "../../../lib/api";
import { createClient } from "../../../lib/supabase/client";

export default function ApplicationsPage() {
  const [applications, setApplications] = useState<Application[]>([]);
  const [message, setMessage] = useState("Loading applications...");
  useEffect(() => {
    createClient().auth.getSession().then(({ data }) => {
      const token = data.session?.access_token;
      if (!token) { setMessage("Sign in to view your applications."); return; }
      api.applications(token).then((items) => { setApplications(items); setMessage(""); }).catch((error: Error) => setMessage(error.message));
    });
  }, []);
  return <main className="min-h-screen bg-[#f5f7f2] px-6 py-10 text-[#1d2725] lg:px-20"><div className="mx-auto max-w-4xl"><p className="text-xs font-semibold uppercase tracking-widest text-[#287067]">Candidate workspace</p><h1 className="mt-2 text-4xl font-semibold">Your applications</h1>{message && <p className="mt-8 text-sm text-[#6c7973]">{message}</p>}<div className="mt-8 space-y-3">{applications.map((application) => <article key={application.id} className="flex items-center justify-between rounded-xl border border-[#dfe6de] bg-white p-5"><div><p className="font-medium">Application {application.id.slice(0, 8)}</p><p className="mt-1 text-sm text-[#6c7973]">Submitted {new Date(application.created_at).toLocaleDateString()}</p></div><span className="rounded-full bg-[#e7f0e6] px-3 py-1 text-xs font-medium text-[#287067]">{application.status}</span></article>)}</div></div></main>;
}
