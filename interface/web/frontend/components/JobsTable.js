"use client";

import { useEffect } from "react";
import { StatusBadge } from "@/components/StatusBadge";

function elapsed(job) {
  const end = job.finished_at ?? Date.now() / 1000;
  const secs = Math.round(end - job.started_at);
  return secs < 60 ? `${secs}s` : `${Math.floor(secs / 60)}m ${secs % 60}s`;
}

export function JobsTable({ jobs, selectedJobId, onSelect, onRefresh }) {
  useEffect(() => {
    const hasActive = jobs.some(
      (j) => j.status === "pending" || j.status === "running"
    );
    if (!hasActive) return;
    const id = setInterval(onRefresh, 1500);
    return () => clearInterval(id);
  }, [jobs, onRefresh]);

  if (jobs.length === 0) {
    return (
      <div className="flex h-full items-center justify-center text-slate-500 text-sm">
        No jobs yet. Launch a run from the sidebar.
      </div>
    );
  }

  return (
    <div className="overflow-auto">
      <table className="w-full text-sm">
        <thead>
          <tr className="border-b border-slate-700 text-left text-xs font-semibold uppercase tracking-wider text-slate-500">
            <th className="px-4 py-3">Run</th>
            <th className="px-4 py-3">Status</th>
            <th className="px-4 py-3">Config</th>
            <th className="px-4 py-3">Elapsed</th>
            <th className="px-4 py-3">Job ID</th>
          </tr>
        </thead>
        <tbody>
          {jobs.map((job) => (
            <tr
              key={job.job_id}
              onClick={() => onSelect(job.job_id)}
              className={`cursor-pointer border-b border-slate-700/50 transition-colors hover:bg-slate-800/60 ${
                selectedJobId === job.job_id ? "bg-slate-800/80" : ""
              }`}
            >
              <td className="px-4 py-3 font-medium text-slate-200">
                {job.run_name}
              </td>
              <td className="px-4 py-3">
                <StatusBadge status={job.status} />
              </td>
              <td className="px-4 py-3 text-slate-400">{job.config_name}</td>
              <td className="px-4 py-3 tabular-nums text-slate-400">
                {elapsed(job)}
              </td>
              <td className="px-4 py-3 font-mono text-xs text-slate-500">
                {job.job_id.slice(0, 8)}…
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
