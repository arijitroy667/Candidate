"use client";

import Link from "next/link";
import { FormEvent, useEffect, useState } from "react";
import { api } from "../../../lib/api";
import { createClient } from "../../../lib/supabase/client";

export default function CandidateProfilePage() {
  const [message, setMessage] = useState("Loading profile...");
  useEffect(() => { createClient().auth.getSession().then(({ data }) => { if (!data.session) { setMessage("Sign in to edit your profile."); return; } api.profile(data.session.access_token).then(() => setMessage("")).catch(() => setMessage("")); }); }, []);
  async function submit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault(); setMessage("Saving profile...");
    const values = new FormData(event.currentTarget); const session = (await createClient().auth.getSession()).data.session;
    if (!session) { setMessage("Sign in to continue."); return; }
    try {
      await api.saveProfile(session.access_token, { headline: String(values.get("headline") || ""), summary: String(values.get("summary") || ""), location: String(values.get("location") || ""), skills: String(values.get("skills") || "").split(",").map((item) => item.trim()).filter(Boolean), experience: [], education: [] });
      const file = values.get("resume"); if (file instanceof File && file.size) await api.uploadResume(session.access_token, file);
      setMessage("Profile and resume saved.");
    } catch (error) { setMessage(error instanceof Error ? error.message : "Unable to save profile."); }
  }
  return <main className="min-h-screen bg-[#f5f7f2] px-6 py-10 text-[#1d2725] lg:px-20"><div className="mx-auto max-w-2xl"><Link href="/jobs" className="text-sm text-[#287067]">← Browse jobs</Link><h1 className="mt-6 text-4xl font-semibold">Candidate profile</h1><p className="mt-3 text-[#6c7973]">Save your basic profile and one PDF or DOCX resume before applying.</p><form onSubmit={submit} className="mt-8 space-y-5 rounded-xl border border-[#dfe6de] bg-white p-6"><Field label="Headline" name="headline" placeholder="Backend engineer" /><Field label="Location" name="location" placeholder="Bengaluru / Remote" /><Field label="Skills" name="skills" placeholder="Python, FastAPI, PostgreSQL" /><label className="block text-sm font-medium">Summary<textarea name="summary" rows={6} className="mt-2 w-full rounded-lg border border-[#dfe6de] p-3" placeholder="A short professional summary" /></label><label className="block text-sm font-medium">Resume<input name="resume" type="file" accept="application/pdf,.docx,application/vnd.openxmlformats-officedocument.wordprocessingml.document" className="mt-2 block w-full rounded-lg border border-[#dfe6de] p-3 text-sm" /></label>{message && <p className="text-sm text-[#287067]">{message}</p>}<button className="rounded-lg bg-[#173f3a] px-5 py-3 text-sm font-medium text-white">Save profile</button></form></div></main>;
}

function Field({ label, name, placeholder }: { label: string; name: string; placeholder?: string }) { return <label className="block text-sm font-medium">{label}<input name={name} placeholder={placeholder} className="mt-2 w-full rounded-lg border border-[#dfe6de] p-3" /></label>; }
