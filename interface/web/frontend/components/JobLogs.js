"use client";

import { useState, useEffect, useRef } from "react";
import { api } from "@/lib/api";
import { extractError } from "@/lib/extractError";
import { StatusBadge } from "@/components/StatusBadge";

export function JobLogs({ jobId }) {
  const [job, setJob] = useState(null);
  const [error, setError] = useState(null);
  const bottomRef = useRef(null);

  useEffect(() => {
    if (!jobId) return;
    setJob(null);
    setError(null);

    let active = true;

    async function poll() {
      try {
        const data = await api.getJob(jobId);
        if (!active) return;
        setJob(data);
        if (data.status === "pending" || data.status === "running") {
          setTimeout(poll, 1500);
        }
      } catch (e) {
        if (active) setError(extractError(e));
      }
    }
    poll();
    return () => {
      active = false;
    };
  }, [jobId]);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [job?.logs]);

  if (!jobId) {
    return (
      <div className="flex h-full items-center justify-center text-slate-500 text-sm">
        Select a job from the table to view its logs.
      </div>
    );
  }

  if (error) {
    return (
      <div className="p-4 text-sm text-red-400">Error: {error}</div>
    );
  }

  if (!job) {
    return (
      <div className="flex h-full items-center justify-center text-slate-500 text-sm">
        Loading…
      </div>
    );
  }

  return (
    <div className="flex h-full flex-col gap-3 p-4">
      {/* Header */}
      <div className="flex flex-wrap items-center gap-3">
        <span className="font-semibold text-slate-200">{job.run_name}</span>
        <StatusBadge status={job.status} />
        <span className="font-mono text-xs text-slate-500">{job.job_id}</span>
      </div>

      {/* Output */}
      {job.output !== null && (
        <div className="rounded-lg border border-slate-700 bg-slate-950 p-3">
          <p className="mb-1 text-xs font-semibold uppercase tracking-wider text-slate-500">
            Output
          </p>
          <pre className="overflow-auto text-xs text-green-300">
            {typeof job.output === "object"
              ? JSON.stringify(job.output, null, 2)
              : String(job.output)}
          </pre>
        </div>
      )}

      {/* Logs */}
      <div className="flex min-h-0 flex-1 flex-col rounded-lg border border-slate-700 bg-slate-950">
        <p className="border-b border-slate-700 px-3 py-1.5 text-xs font-semibold uppercase tracking-wider text-slate-500">
          Logs
        </p>
        <div className="flex-1 overflow-auto p-3">
          {job.logs.length === 0 ? (
            <p className="text-xs text-slate-600">No log lines yet.</p>
          ) : (
            job.logs.map((line, i) => (
              <p key={i} className="font-mono text-xs leading-relaxed text-slate-300">
                {line}
              </p>
            ))
          )}
          <div ref={bottomRef} />
        </div>
      </div>
    </div>
  );
}
