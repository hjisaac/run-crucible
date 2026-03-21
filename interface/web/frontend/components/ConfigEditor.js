"use client";

import { useState, useEffect } from "react";
import { api } from "@/lib/api";
import { extractError } from "@/lib/extractError";

export function ConfigEditor({ runName }) {
  const [content, setContent] = useState("");
  const [original, setOriginal] = useState("");
  const [loading, setLoading] = useState(false);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState(null);
  const [saved, setSaved] = useState(false);

  useEffect(() => {
    if (!runName) return;
    setLoading(true);
    setError(null);
    setSaved(false);
    api
      .getConfig(runName)
      .then(({ content }) => {
        setContent(content);
        setOriginal(content);
      })
      .catch((e) => setError(extractError(e)))
      .finally(() => setLoading(false));
  }, [runName]);

  const dirty = content !== original;

  async function handleSave() {
    setSaving(true);
    setSaved(false);
    setError(null);
    try {
      await api.saveConfig(runName, content);
      setOriginal(content);
      setSaved(true);
      setTimeout(() => setSaved(false), 2000);
    } catch (e) {
      setError(extractError(e));
    } finally {
      setSaving(false);
    }
  }

  if (!runName) {
    return (
      <div className="flex h-full items-center justify-center text-slate-500">
        Select a run to view its config.
      </div>
    );
  }

  return (
    <div className="flex h-full flex-col gap-3 p-4">
      <div className="flex items-center justify-between">
        <h2 className="text-sm font-semibold text-slate-200">
          <span className="text-slate-500">Config · </span>
          {runName}
        </h2>
        <div className="flex items-center gap-2">
          {error && <span className="text-xs text-red-400">{error}</span>}
          {saved && (
            <span className="text-xs text-green-400">Saved ✓</span>
          )}
          <button
            disabled={!dirty || saving}
            onClick={handleSave}
            className="rounded-md bg-indigo-600 px-3 py-1.5 text-xs font-semibold text-white transition-colors hover:bg-indigo-500 disabled:cursor-not-allowed disabled:opacity-40"
          >
            {saving ? "Saving…" : "Save"}
          </button>
        </div>
      </div>

      {loading ? (
        <div className="flex flex-1 items-center justify-center text-slate-500 text-sm">
          Loading…
        </div>
      ) : (
        <textarea
          value={content}
          onChange={(e) => setContent(e.target.value)}
          spellCheck={false}
          className="flex-1 resize-none rounded-lg border border-slate-700 bg-slate-950 p-3 font-mono text-sm text-slate-200 outline-none focus:border-indigo-500 focus:ring-1 focus:ring-indigo-500"
        />
      )}
    </div>
  );
}
