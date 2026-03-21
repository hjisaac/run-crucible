import axios from "axios";

/**
 * Pre-configured axios instance.
 *
 * In development `NEXT_PUBLIC_API_BASE_URL` is set to `http://localhost:8000`
 * so requests reach the local FastAPI server. In production the static export
 * is served by FastAPI itself, so all `/api/…` calls resolve on the same
 * origin and no base URL is needed.
 */
const client = axios.create({
  baseURL: process.env.NEXT_PUBLIC_API_BASE_URL || "",
  headers: { "Content-Type": "application/json" },
});

export const api = {
  /** List all discovered run names. */
  getRuns: () =>
    client.get("/api/runs").then((r) => r.data),

  /** Get YAML config content for a run. */
  getConfig: (runName, configName = "default") =>
    client
      .get(`/api/runs/${runName}/config`, { params: { config: configName } })
      .then((r) => r.data),

  /** Overwrite the YAML config for a run. */
  saveConfig: (runName, content, configName = "default") =>
    client
      .put(
        `/api/runs/${runName}/config`,
        { content },
        { params: { config: configName } }
      )
      .then((r) => r.data),

  /** Launch a run and return { job_id }. */
  launchRun: (runName, configName = "default", overrides = []) =>
    client
      .post(`/api/runs/${runName}/launch`, { config: configName, overrides })
      .then((r) => r.data),

  /** List all jobs (most recent first). */
  getJobs: () =>
    client.get("/api/jobs").then((r) => r.data),

  /** Get a single job record including logs. */
  getJob: (jobId) =>
    client.get(`/api/jobs/${jobId}`).then((r) => r.data),
};
