export default function Home() {
  const navigation = [
    ["⌂", "Overview", true],
    ["▣", "Jobs", false],
    ["◌", "Candidates", false],
    ["◇", "Assessments", false],
    ["↗", "Reports", false],
  ] as const;

  return (
    <div className="min-h-full bg-[#f5f7f2] text-[#1d2725]">
      <aside className="fixed inset-y-0 left-0 hidden w-64 border-r border-[#dfe6de] bg-[#fbfcf8] px-6 py-7 lg:block">
        <div className="flex items-center gap-3 text-lg font-semibold tracking-tight">
          <span className="grid size-9 place-items-center rounded-xl bg-[#173f3a] text-sm text-[#d8f36b]">
            cx
          </span>
          candidex
        </div>
        <p className="mt-16 text-[11px] font-semibold uppercase tracking-[0.2em] text-[#82908a]">
          Workspace
        </p>
        <nav className="mt-4 space-y-1 text-sm">
          {navigation.map(([icon, label, active]) => (
            <a
              key={label}
              className={`flex items-center gap-3 rounded-lg px-3 py-2.5 ${active ? "bg-[#e7f0e6] font-medium text-[#173f3a]" : "text-[#6c7973] hover:bg-[#f0f4ed]"}`}
              href="#"
            >
              <span className="w-4 text-center text-base">{icon}</span>
              {label}
            </a>
          ))}
        </nav>
        <div className="absolute bottom-7 left-6 right-6 border-t border-[#dfe6de] pt-5 text-sm text-[#6c7973]">
          <a className="flex items-center gap-3 px-3 py-2" href="#">
            ⚙ Settings
          </a>
          <div className="mt-7 flex items-center gap-3">
            <span className="grid size-8 place-items-center rounded-full bg-[#efc7a8] text-xs font-semibold">
              AR
            </span>
            <span>
              <strong className="block text-[#293733]">Alex Rivera</strong>
              <small>Admin</small>
            </span>
          </div>
        </div>
      </aside>
      <main className="mx-auto max-w-7xl px-6 py-8 lg:ml-64 lg:px-12">
        <header className="flex items-start justify-between">
          <div>
            <p className="text-xs font-semibold uppercase tracking-[0.18em] text-[#82908a]">
              Wednesday, September 3, 2026
            </p>
            <h1 className="mt-2 text-3xl font-semibold tracking-tight">
              Good morning, Alex.
            </h1>
            <p className="mt-2 text-sm text-[#6c7973]">
              Here&apos;s what needs your attention today.
            </p>
          </div>
          <button className="rounded-lg bg-[#173f3a] px-4 py-2.5 text-sm font-medium text-white shadow-sm hover:bg-[#245952]">
            + Create job
          </button>
        </header>
        <section className="mt-10 grid gap-4 sm:grid-cols-2 xl:grid-cols-4">
          {[
            ["Active jobs", "12", "+2 this month", "#d8f36b"],
            ["Total candidates", "284", "+18 this week", "#cce5ed"],
            ["Awaiting review", "37", "Needs attention", "#f4d7b6"],
            [
              "Avg. time to shortlist",
              "4.2d",
              "↓ 0.8d vs last month",
              "#e3d7ef",
            ],
          ].map(([label, value, note, color]) => (
            <div
              key={label}
              className="rounded-xl border border-[#dfe6de] bg-white p-5"
            >
              <div className="flex items-start justify-between">
                <p className="text-sm text-[#6c7973]">{label}</p>
                <span
                  className="size-2.5 rounded-full"
                  style={{ backgroundColor: color }}
                />
              </div>
              <p className="mt-5 text-3xl font-semibold tracking-tight">
                {value}
              </p>
              <p className="mt-2 text-xs text-[#6c7973]">{note}</p>
            </div>
          ))}
        </section>
        <section className="mt-8 grid gap-6 xl:grid-cols-[1.4fr_1fr]">
          <div className="rounded-xl border border-[#dfe6de] bg-white p-6">
            <div className="flex items-center justify-between">
              <div>
                <h2 className="font-semibold">Hiring pipeline</h2>
                <p className="mt-1 text-sm text-[#6c7973]">All active roles</p>
              </div>
              <button className="text-sm font-medium text-[#287067]">
                View jobs →
              </button>
            </div>
            <div className="mt-8 grid grid-cols-5 gap-3">
              {[
                ["Applied", "128", "#cce5ed"],
                ["Screening", "64", "#d8f36b"],
                ["Assessment", "39", "#f4d7b6"],
                ["Interview", "16", "#e3d7ef"],
                ["Shortlist", "8", "#b8dfcb"],
              ].map(([stage, count, color]) => (
                <div key={stage}>
                  <div className="flex h-36 items-end rounded-lg bg-[#f5f7f2] p-2">
                    <div
                      className="w-full rounded-md"
                      style={{
                        height: `${Math.max(20, (Number(count) / 128) * 100)}%`,
                        backgroundColor: color,
                      }}
                    />
                  </div>
                  <p className="mt-3 text-xs text-[#6c7973]">{stage}</p>
                  <p className="mt-1 text-lg font-semibold">{count}</p>
                </div>
              ))}
            </div>
          </div>
          <div className="rounded-xl border border-[#dfe6de] bg-[#173f3a] p-6 text-white">
            <div className="flex items-center justify-between">
              <h2 className="font-semibold">Needs your review</h2>
              <span className="rounded-full bg-[#d8f36b] px-2.5 py-1 text-xs font-semibold text-[#173f3a]">
                37
              </span>
            </div>
            <p className="mt-2 text-sm text-[#bdd0c8]">
              Candidates flagged for low confidence or an exceptional signal.
            </p>
            <div className="mt-7 space-y-4">
              {[
                ["Jordan Lee", "Backend Engineer", "82%"],
                ["Maya Chen", "ML Engineer", "68%"],
                ["Sam Okafor", "Product Designer", "74%"],
              ].map(([name, role, confidence]) => (
                <div
                  key={name}
                  className="flex items-center justify-between border-b border-white/10 pb-4"
                >
                  <div>
                    <p className="text-sm font-medium">{name}</p>
                    <p className="mt-1 text-xs text-[#9db7ad]">{role}</p>
                  </div>
                  <span className="text-xs text-[#d8f36b]">
                    {confidence} confidence
                  </span>
                </div>
              ))}
            </div>
            <button className="mt-6 text-sm font-medium text-[#d8f36b]">
              Open review queue →
            </button>
          </div>
        </section>
        <section className="mt-6 rounded-xl border border-[#dfe6de] bg-white p-6">
          <div className="flex items-center justify-between">
            <div>
              <h2 className="font-semibold">Active jobs</h2>
              <p className="mt-1 text-sm text-[#6c7973]">
                Your team&apos;s open hiring workflows
              </p>
            </div>
            <button className="text-sm font-medium text-[#287067]">
              See all →
            </button>
          </div>
          <div className="mt-6 overflow-x-auto">
            <table className="w-full min-w-155 text-left text-sm">
              <thead className="border-b border-[#e7ece5] text-xs uppercase tracking-wider text-[#82908a]">
                <tr>
                  <th className="pb-3 font-medium">Role</th>
                  <th className="pb-3 font-medium">Candidates</th>
                  <th className="pb-3 font-medium">In review</th>
                  <th className="pb-3 font-medium">Updated</th>
                  <th className="pb-3 font-medium">Status</th>
                </tr>
              </thead>
              <tbody>
                {[
                  ["Senior Backend Engineer", "42", "8", "Today", "Hiring"],
                  ["Product Designer", "31", "5", "Yesterday", "Hiring"],
                  ["ML Engineer", "27", "3", "Aug 30", "Hiring"],
                ].map(([role, candidates, review, updated, status]) => (
                  <tr
                    key={role}
                    className="border-b border-[#eef1ec] last:border-0"
                  >
                    <td className="py-4 font-medium">
                      {role}
                      <span className="mt-1 block text-xs font-normal text-[#82908a]">
                        Engineering · Remote
                      </span>
                    </td>
                    <td className="py-4">{candidates}</td>
                    <td className="py-4">{review}</td>
                    <td className="py-4 text-[#6c7973]">{updated}</td>
                    <td className="py-4">
                      <span className="rounded-full bg-[#e7f0e6] px-2.5 py-1 text-xs font-medium text-[#287067]">
                        {status}
                      </span>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </section>
      </main>
    </div>
  );
}
