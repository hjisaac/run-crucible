"use client";

export function RunList({ runs, selectedRun, onSelect, onLaunch, launching }) {
  return (
    <aside className="flex h-full w-64 shrink-0 flex-col border-r border-slate-700/60 bg-slate-900">
      <div className="border-b border-slate-700/60 px-4 py-3">
        <p className="text-xs font-semibold uppercase tracking-widest text-slate-500">
          Runs
        </p>
      </div>

      <nav className="flex-1 overflow-y-auto p-2">
        {runs.length === 0 && (
          <p className="px-2 py-4 text-center text-sm text-slate-500">
            No runs discovered.
          </p>
        )}
        {runs.map((name) => (
          <div
            key={name}
            className={`group flex items-center justify-between rounded-lg px-3 py-2 text-sm transition-colors ${
              selectedRun === name
                ? "bg-indigo-600/20 text-indigo-300"
                : "text-slate-300 hover:bg-slate-800 hover:text-white"
            }`}
          >
            <button
              className="flex-1 text-left font-medium"
              onClick={() => onSelect(name)}
            >
              {name}
            </button>
            <button
              disabled={launching === name}
              onClick={() => onLaunch(name)}
              className="ml-2 rounded-md bg-indigo-600 px-2 py-1 text-xs font-semibold text-white transition-colors hover:bg-indigo-500 disabled:cursor-not-allowed disabled:opacity-50"
            >
              {launching === name ? "…" : "Run"}
            </button>
          </div>
        ))}
      </nav>
    </aside>
  );
}
