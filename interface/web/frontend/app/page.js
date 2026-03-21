"use client";

import { useState, useEffect, useCallback } from "react";
import { api } from "@/lib/api";
import { extractError } from "@/lib/extractError";
import { RunList } from "@/components/RunList";
import { ConfigEditor } from "@/components/ConfigEditor";
import { JobsTable } from "@/components/JobsTable";
import { JobLogs } from "@/components/JobLogs";

const TABS = ["Config", "Jobs", "Logs"];

export default function Home() {
  const [runs, setRuns] = useState([]);
  const [runsError, setRunsError] = useState(null);

  const [selectedRun, setSelectedRun] = useState(null);
  const [launching, setLaunching] = useState(null);
  const [launchError, setLaunchError] = useState(null);

  const [activeTab, setActiveTab] = useState("Config");
  const [jobs, setJobs] = useState([]);
  const [selectedJobId, setSelectedJobId] = useState(null);

  // Load run list once on mount
  useEffect(() => {
    api
      .getRuns()
      .then(({ runs }) => setRuns(runs))
      .catch((e) => setRunsError(extractError(e)));
  }, []);

  const refreshJobs = useCallback(() => {
    api.getJobs().then(({ jobs }) => setJobs(jobs));
  }, []);

  // Refresh jobs when the Jobs or Logs tab is active
  useEffect(() => {
    if (activeTab === "Jobs" || activeTab === "Logs") {
      refreshJobs();
    }
  }, [activeTab, refreshJobs]);

  async function handleLaunch(runName) {
    setLaunching(runName);
    setLaunchError(null);
    try {
      const { job_id } = await api.launchRun(runName);
      setSelectedJobId(job_id);
      setActiveTab("Logs");
      refreshJobs();
    } catch (e) {
      setLaunchError(extractError(e));
    } finally {
      setLaunching(null);
    }
  }

  function handleSelectRun(name) {
    setSelectedRun(name);
    setActiveTab("Config");
  }

  function handleSelectJob(jobId) {
    setSelectedJobId(jobId);
    setActiveTab("Logs");
  }

  return (
    <div className="flex h-full flex-col">
      {/* Top nav */}
      <header className="flex h-12 shrink-0 items-center gap-3 border-b border-slate-700/60 bg-slate-900 px-4">
        <span className="text-lg font-bold tracking-tight text-white">
          🔥 Crucible
        </span>
        <span className="rounded-full bg-indigo-600/20 px-2 py-0.5 text-xs font-medium text-indigo-300">
          Web Interface
        </span>
        <div className="flex-1" />
        {launchError && (
          <span className="text-xs text-red-400">Launch failed: {launchError}</span>
        )}
        {runsError && (
          <span className="text-xs text-red-400">Could not load runs: {runsError}</span>
        )}
      </header>

      {/* Body */}
      <div className="flex min-h-0 flex-1">
        {/* Sidebar */}
        <RunList
          runs={runs}
          selectedRun={selectedRun}
          onSelect={handleSelectRun}
          onLaunch={handleLaunch}
          launching={launching}
        />

        {/* Main content */}
        <main className="flex min-w-0 flex-1 flex-col">
          {/* Tabs */}
          <div className="flex shrink-0 border-b border-slate-700/60 bg-slate-900/50 px-2">
            {TABS.map((tab) => (
              <button
                key={tab}
                onClick={() => setActiveTab(tab)}
                className={`px-4 py-3 text-sm font-medium transition-colors ${
                  activeTab === tab
                    ? "border-b-2 border-indigo-500 text-white"
                    : "text-slate-400 hover:text-slate-200"
                }`}
              >
                {tab}
                {tab === "Jobs" && jobs.length > 0 && (
                  <span className="ml-1.5 rounded-full bg-slate-700 px-1.5 py-0.5 text-xs text-slate-300">
                    {jobs.length}
                  </span>
                )}
              </button>
            ))}
          </div>

          {/* Tab panels */}
          <div className="min-h-0 flex-1 overflow-auto">
            {activeTab === "Config" && (
              <ConfigEditor runName={selectedRun} />
            )}
            {activeTab === "Jobs" && (
              <JobsTable
                jobs={jobs}
                selectedJobId={selectedJobId}
                onSelect={handleSelectJob}
                onRefresh={refreshJobs}
              />
            )}
            {activeTab === "Logs" && (
              <JobLogs jobId={selectedJobId} />
            )}
          </div>
        </main>
      </div>
    </div>
  );
}
