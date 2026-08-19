"use client";

import { FormEvent, useEffect, useMemo, useState } from "react";
import {
  AdditionalResumeEvidenceRequest,
  AuthLoginResponse,
  AuthStatusResponse,
  AnalysisResponse,
  JobImportResponse,
  JobListItem,
  JobPreviewResponse,
  ResumeEvidence,
  JobRequirementExtractionResponse,
  ResumeExtractionResponse,
  ResumeUploadResponse,
  ApiRequestError,
  apiRequest,
  clearAccessToken,
  getAccessToken,
  setAccessToken,
} from "../lib/api";

type JobMode = "manual" | "url";
type CurrentJob = JobImportResponse | JobPreviewResponse;

type BusyAction =
  | "boot"
  | "unlock"
  | "upload-resume"
  | "extract-resume"
  | "add-evidence"
  | "delete-evidence"
  | "delete-resume"
  | "create-job"
  | "extract-job"
  | "analyze"
  | "load-analysis"
  | "delete-job"
  | null;

const defaultDescription =
  "We need a backend intern with Python, SQL, Git, REST APIs, tests, and communication skills. Docker is preferred.";

export default function Home() {
  const [busyAction, setBusyAction] = useState<BusyAction>("boot");
  const [error, setError] = useState<string | null>(null);
  const [resume, setResume] = useState<ResumeUploadResponse | null>(null);
  const [resumeExtraction, setResumeExtraction] = useState<ResumeExtractionResponse | null>(null);
  const [job, setJob] = useState<CurrentJob | null>(null);
  const [jobs, setJobs] = useState<JobListItem[]>([]);
  const [requirements, setRequirements] = useState<JobRequirementExtractionResponse | null>(null);
  const [analysis, setAnalysis] = useState<AnalysisResponse | null>(null);
  const [jobMode, setJobMode] = useState<JobMode>("manual");
  const [shouldSaveJob, setShouldSaveJob] = useState(false);
  const [jobTitle, setJobTitle] = useState("Backend Intern");
  const [company, setCompany] = useState("Example Corp");
  const [description, setDescription] = useState(defaultDescription);
  const [url, setUrl] = useState("");
  const [deletingJobId, setDeletingJobId] = useState<number | null>(null);
  const [deletingEvidenceId, setDeletingEvidenceId] = useState<number | null>(null);
  const [additionalSkill, setAdditionalSkill] = useState("");
  const [additionalEvidence, setAdditionalEvidence] = useState("");
  const [accessRequired, setAccessRequired] = useState(false);
  const [accessGranted, setAccessGranted] = useState(false);
  const [demoLoginEnabled, setDemoLoginEnabled] = useState(false);
  const [loginUsername, setLoginUsername] = useState("");
  const [accessTokenInput, setAccessTokenInput] = useState("");

  useEffect(() => {
    void initializeWorkspace();
  }, []);

  const status = useMemo(() => {
    if (busyAction) return "Working";
    if (analysis) return "Analysis ready";
    if (requirements) return "Requirements ready";
    if (job && resumeExtraction) return "Ready";
    if (jobs.length || resume) return "Loaded";
    return "Local MVP";
  }, [analysis, busyAction, job, jobs.length, requirements, resume, resumeExtraction]);

  const matchSummary = useMemo(() => {
    const summary = { match: 0, partial: 0, noMatch: 0 };
    for (const item of analysis?.matches ?? []) {
      if (item.classification === "MATCH") summary.match += 1;
      if (item.classification === "PARTIAL") summary.partial += 1;
      if (item.classification === "NO_MATCH") summary.noMatch += 1;
    }
    return summary;
  }, [analysis]);
  const requirementCount = requirements?.requirements.length ?? analysis?.matches.length ?? 0;

  async function runAction<T>(action: BusyAction, task: () => Promise<T>): Promise<T | null> {
    setBusyAction(action);
    setError(null);
    try {
      return await task();
    } catch (caught) {
      if (caught instanceof ApiRequestError && caught.status === 401) {
        clearAccessToken();
        setAccessRequired(true);
        setAccessGranted(false);
        setError("Enter the shared password to continue.");
        return null;
      }
      setError(caught instanceof Error ? caught.message : "Unexpected error");
      return null;
    } finally {
      setBusyAction(null);
    }
  }

  async function initializeWorkspace() {
    setBusyAction("boot");
    setError(null);
    try {
      const authStatus = await apiRequest<AuthStatusResponse>("/auth/status");
      setAccessRequired(authStatus.access_required);
      setDemoLoginEnabled(authStatus.demo_login_enabled);
      if (authStatus.demo_username) setLoginUsername(authStatus.demo_username);
      if (authStatus.access_required && !getAccessToken()) {
        setAccessGranted(false);
        return;
      }

      setAccessGranted(true);
      await loadWorkspaceData();
    } catch (caught) {
      setError(caught instanceof Error ? caught.message : "Unexpected error");
      setAccessGranted(false);
    } finally {
      setBusyAction(null);
    }
  }

  async function loadWorkspace() {
    const result = await runAction("boot", loadWorkspaceData);
    if (result) setAccessGranted(true);
  }

  async function loadWorkspaceData() {
    const [resumeResult, jobsResult] = await Promise.allSettled([
      apiRequest<ResumeUploadResponse>("/resumes/current"),
      apiRequest<JobListItem[]>("/jobs"),
    ]);

    if (resumeResult.status === "fulfilled") setResume(resumeResult.value);
    if (resumeResult.status === "fulfilled") {
      const evidenceResult = await apiRequest<ResumeExtractionResponse>(
        `/resumes/${resumeResult.value.resume_id}/evidence`,
      ).catch(() => null);
      setResumeExtraction(evidenceResult?.evidence.length ? evidenceResult : null);
    }
    if (jobsResult.status === "rejected") throw jobsResult.reason;
    if (jobsResult.status === "fulfilled") {
      setJobs(jobsResult.value);
      if (jobsResult.value[0]) setJob(jobListItemToJob(jobsResult.value[0]));
    }
    return true;
  }

  async function refreshJobs() {
    const result = await apiRequest<JobListItem[]>("/jobs");
    setJobs(result);
    return result;
  }

  async function handleResumeUpload(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const form = event.currentTarget;
    const fileInput = form.elements.namedItem("resume") as HTMLInputElement;
    const file = fileInput.files?.[0];
    if (!file) {
      setError("Choose a PDF resume first.");
      return;
    }

    const data = new FormData();
    data.append("file", file);

    const result = await runAction("upload-resume", () =>
      apiRequest<ResumeUploadResponse>("/resumes/upload", {
        method: "POST",
        body: data,
      }),
    );
    if (result) {
      setResume(result);
      setResumeExtraction(null);
      setAnalysis(null);
    }
  }

  async function handleDeleteResume() {
    if (!resume) return;
    if (!window.confirm("Delete this resume and all extracted items?")) return;

    const deleted = await runAction("delete-resume", async () => {
      await apiRequest<void>(`/resumes/${resume.resume_id}`, { method: "DELETE" });
      return true;
    });

    if (deleted) {
      setResume(null);
      setResumeExtraction(null);
      setAnalysis(null);
    }
  }

  async function handleUnlock(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();

    if (demoLoginEnabled) {
      const username = loginUsername.trim();
      const password = accessTokenInput.trim();
      if (!username || !password) {
        setError("Enter the demo username and password.");
        return;
      }

      const login = await runAction("unlock", () =>
        apiRequest<AuthLoginResponse>("/auth/login", {
          method: "POST",
          body: JSON.stringify({ username, password }),
        }),
      );
      if (!login) return;

      setAccessToken(login.access_token);
    } else {
      const token = accessTokenInput.trim();
      if (!token) {
        setError("Enter the access password.");
        return;
      }
      setAccessToken(token);
    }

    const loaded = await runAction("unlock", loadWorkspaceData);
    if (loaded) {
      setAccessGranted(true);
      setAccessTokenInput("");
      return;
    }

    clearAccessToken();
    setAccessGranted(false);
  }

  function handleLock() {
    clearAccessToken();
    setAccessGranted(false);
    setResume(null);
    setResumeExtraction(null);
    setJob(null);
    setJobs([]);
    setRequirements(null);
    setAnalysis(null);
  }

  async function handleResumeExtraction() {
    if (!resume) return;
    const result = await runAction("extract-resume", () =>
      apiRequest<ResumeExtractionResponse>(`/resumes/${resume.resume_id}/extract`, {
        method: "POST",
      }),
    );
    if (result) {
      setResumeExtraction(result);
      setAnalysis(null);
    }
  }

  async function handleAddResumeEvidence(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (!resume) return;

    const payload: AdditionalResumeEvidenceRequest = {
      skill: additionalSkill.trim(),
      evidence_text: additionalEvidence.trim(),
    };
    if (!payload.skill || !payload.evidence_text) {
      setError("Add a context name and a short explanation.");
      return;
    }

    const result = await runAction("add-evidence", () =>
      apiRequest<ResumeEvidence>(`/resumes/${resume.resume_id}/evidence`, {
        method: "POST",
        body: JSON.stringify(payload),
      }),
    );
    if (result) {
      setResumeExtraction((current) => ({
        resume_id: resume.resume_id,
        filename: resume.filename,
        evidence: [...(current?.evidence ?? []), result],
      }));
      setAdditionalSkill("");
      setAdditionalEvidence("");
      setAnalysis(null);
    }
  }

  async function handleDeleteResumeEvidence(evidenceId: number) {
    if (!resume) return;
    if (!window.confirm("Remove this resume item?")) return;

    setDeletingEvidenceId(evidenceId);
    const deleted = await runAction("delete-evidence", async () => {
      await apiRequest<void>(`/resumes/${resume.resume_id}/evidence/${evidenceId}`, {
        method: "DELETE",
      });
      return true;
    });
    setDeletingEvidenceId(null);

    if (deleted) {
      setResumeExtraction((current) =>
        current
          ? {
              ...current,
              evidence: current.evidence.filter((item) => item.id !== evidenceId),
            }
          : current,
      );
      setAnalysis(null);
    }
  }

  async function handleCreateJob(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const result = await runAction("create-job", () => {
      if (jobMode === "url") {
        return apiRequest<CurrentJob>(shouldSaveJob ? "/jobs/import-url" : "/jobs/preview-url", {
          method: "POST",
          body: JSON.stringify({ url }),
        });
      }

      if (!shouldSaveJob) {
        const cleanDescription = description.trim().replace(/\s+/g, " ");
        return Promise.resolve<JobPreviewResponse>({
          source_type: "manual",
          url: null,
          title: jobTitle || null,
          company: company || null,
          scrape_status: null,
          character_count: cleanDescription.length,
          preview: cleanDescription.slice(0, 1200),
          description: cleanDescription,
        });
      }

      return apiRequest<JobImportResponse>("/jobs/manual", {
        method: "POST",
        body: JSON.stringify({
          title: jobTitle || null,
          company: company || null,
          description,
        }),
      });
    });

    if (result) {
      setJob(result);
      setRequirements(null);
      setAnalysis(null);
      if (isSavedJob(result)) await refreshJobs();
    }
  }

  async function handleExtractRequirements() {
    if (!job) return;
    const result = await runAction("extract-job", () => {
      if (isSavedJob(job)) {
        return apiRequest<JobRequirementExtractionResponse>(
          `/jobs/${job.job_id}/extract-requirements`,
          {
            method: "POST",
          },
        );
      }

      return apiRequest<JobRequirementExtractionResponse>("/jobs/extract-requirements", {
        method: "POST",
        body: JSON.stringify({
          title: job.title,
          company: job.company,
          description: job.description,
        }),
      });
    });
    if (result) {
      setRequirements(result);
      setAnalysis(null);
    }
  }

  async function handleAnalyze() {
    if (!job || !isSavedJob(job)) return;
    const result = await runAction("analyze", () =>
      apiRequest<AnalysisResponse>(`/jobs/${job.job_id}/analyze`, {
        method: "POST",
      }),
    );
    if (result) setAnalysis(result);
  }

  async function handleLoadSavedAnalysis() {
    if (!job || !isSavedJob(job)) return;
    const result = await runAction("load-analysis", () =>
      apiRequest<AnalysisResponse>(`/jobs/${job.job_id}/analysis`),
    );
    if (result) setAnalysis(result);
  }

  async function handleDeleteJob(jobId: number) {
    if (!window.confirm("Delete this saved job?")) return;

    setDeletingJobId(jobId);
    const deleted = await runAction("delete-job", async () => {
      await apiRequest<void>(`/jobs/${jobId}`, { method: "DELETE" });
      return true;
    });
    setDeletingJobId(null);

    if (deleted) {
      const nextJobs = jobs.filter((item) => item.job_id !== jobId);
      setJobs(nextJobs);
      if (isSavedJob(job) && job.job_id === jobId) {
        setJob(nextJobs[0] ? jobListItemToJob(nextJobs[0]) : null);
        setRequirements(null);
        setAnalysis(null);
      }
    }
  }

  function selectJob(item: JobListItem) {
    setJob(jobListItemToJob(item));
    setRequirements(null);
    setAnalysis(null);
  }

  if (accessRequired && !accessGranted) {
    return (
      <main className="shell access-shell">
        <section className="access-panel">
          <p className="eyebrow">ApplyAI</p>
          <h1>{demoLoginEnabled ? "Demo Access" : "Private Access"}</h1>
          <p>
            {demoLoginEnabled
              ? "Use the test login to open a workspace with demo data."
              : "Enter the shared password to open the workspace."}
          </p>
          {error ? <div className="error-banner">{error}</div> : null}
          <form className="stack" onSubmit={handleUnlock}>
            {demoLoginEnabled ? (
              <input
                autoFocus
                onChange={(event) => setLoginUsername(event.target.value)}
                placeholder="Username"
                type="text"
                value={loginUsername}
              />
            ) : null}
            <input
              autoFocus={!demoLoginEnabled}
              onChange={(event) => setAccessTokenInput(event.target.value)}
              placeholder={demoLoginEnabled ? "Password" : "Access password"}
              type="password"
              value={accessTokenInput}
            />
            <button disabled={busyAction !== null} type="submit">
              {busyAction === "unlock" ? "Opening..." : "Open Workspace"}
            </button>
          </form>
        </section>
      </main>
    );
  }

  return (
    <main className="shell">
      <section className="workspace">
        <div className="toolbar">
          <div>
            <p className="eyebrow">ApplyAI</p>
            <h1>Job match workspace</h1>
          </div>
          <div className="toolbar-actions">
            <button className="secondary-button" onClick={loadWorkspace} type="button">
              Refresh
            </button>
            {accessRequired ? (
              <button className="secondary-button" onClick={handleLock} type="button">
                Access
              </button>
            ) : null}
            <span className="status">{status}</span>
          </div>
        </div>

        {error ? <div className="error-banner">{error}</div> : null}

        <details className="help-panel">
          <summary>Help</summary>
          <div className="help-grid">
            <div>
              <strong>1. Resume</strong>
              <span>Upload the PDF, extract evidence, then add missing context if needed.</span>
            </div>
            <div>
              <strong>2. Job</strong>
              <span>Paste a job or import a URL. Saved jobs can be analyzed and reused.</span>
            </div>
            <div>
              <strong>3. Analysis</strong>
              <span>Extract requirements first, then run the match for saved jobs.</span>
            </div>
          </div>
        </details>

        <section className="metrics-strip">
          <div>
            <span>Resume</span>
            <strong>{resume ? "Uploaded" : "None"}</strong>
          </div>
          <div>
            <span>Saved Jobs</span>
            <strong>{jobs.length}</strong>
          </div>
          <div>
            <span>Latest Score</span>
            <strong>{analysis ? `${analysis.score}%` : "--"}</strong>
          </div>
          <div>
            <span>Requirements</span>
            <strong>{requirementCount}</strong>
          </div>
        </section>

        <div className="grid">
          <section className="panel">
            <div className="panel-header">
              <h2>Resume</h2>
              {resume ? <span className="pill">Uploaded</span> : null}
            </div>

            <form className="stack" onSubmit={handleResumeUpload}>
              <input name="resume" type="file" accept="application/pdf" />
              <button disabled={busyAction !== null} type="submit">
                {busyAction === "upload-resume" ? "Uploading..." : "Upload PDF"}
              </button>
            </form>

            {resume ? (
              <div className="result-block">
                <strong>{resume.filename}</strong>
                <span>{resume.character_count} characters extracted</span>
                <p>{resume.preview}</p>
                <div className="button-row">
                  <button
                    disabled={busyAction !== null}
                    onClick={handleResumeExtraction}
                    type="button"
                  >
                    {busyAction === "extract-resume" ? "Extracting..." : "Extract Evidence"}
                  </button>
                  <button
                    className="danger-button"
                    disabled={busyAction !== null}
                    onClick={() => void handleDeleteResume()}
                    type="button"
                  >
                    {busyAction === "delete-resume" ? "Deleting..." : "Delete Resume"}
                  </button>
                </div>
              </div>
            ) : null}

            {resumeExtraction ? (
              <div className="list compact-list">
                {resumeExtraction.evidence.map((item) => (
                  <div className="list-row evidence-row" key={item.id}>
                    <div className="evidence-heading">
                      <strong>{item.skill}</strong>
                      <div className="evidence-actions">
                        {item.source === "manual" ? <span className="mini-pill">Manual</span> : null}
                        <button
                          className="danger-button small-danger-button"
                          disabled={busyAction !== null}
                          onClick={() => void handleDeleteResumeEvidence(item.id)}
                          type="button"
                        >
                          {deletingEvidenceId === item.id ? "Removing..." : "Remove"}
                        </button>
                      </div>
                    </div>
                    <span>{item.evidence_text}</span>
                  </div>
                ))}
              </div>
            ) : null}

            {resume ? (
              <form className="stack additional-context" onSubmit={handleAddResumeEvidence}>
                <div>
                  <h3>Additional Context</h3>
                  <p>Availability, authorization, relocation, languages, preferences.</p>
                </div>
                <input
                  onChange={(event) => setAdditionalSkill(event.target.value)}
                  placeholder="Availability"
                  value={additionalSkill}
                />
                <textarea
                  onChange={(event) => setAdditionalEvidence(event.target.value)}
                  placeholder="Available for a full-time internship from January 2027."
                  rows={3}
                  value={additionalEvidence}
                />
                <button disabled={busyAction !== null} type="submit">
                  {busyAction === "add-evidence" ? "Adding..." : "Add Context"}
                </button>
              </form>
            ) : null}
          </section>

          <section className="panel">
            <div className="panel-header">
              <h2>Job</h2>
              {job ? (
                <span className="pill">{isSavedJob(job) ? "Saved" : "Draft"}</span>
              ) : null}
            </div>

            <div className="segmented" role="tablist">
              <button
                className={jobMode === "manual" ? "active" : ""}
                onClick={() => setJobMode("manual")}
                type="button"
              >
                Manual
              </button>
              <button
                className={jobMode === "url" ? "active" : ""}
                onClick={() => setJobMode("url")}
                type="button"
              >
                URL
              </button>
            </div>

            <form className="stack" onSubmit={handleCreateJob}>
              {jobMode === "manual" ? (
                <>
                  <input
                    onChange={(event) => setJobTitle(event.target.value)}
                    placeholder="Role"
                    value={jobTitle}
                  />
                  <input
                    onChange={(event) => setCompany(event.target.value)}
                    placeholder="Company"
                    value={company}
                  />
                  <textarea
                    onChange={(event) => setDescription(event.target.value)}
                    placeholder="Job description"
                    rows={7}
                    value={description}
                  />
                </>
              ) : (
                <input
                  onChange={(event) => setUrl(event.target.value)}
                  placeholder="https://company.com/jobs/backend-intern"
                  type="url"
                  value={url}
                />
              )}
              <label className="checkbox-row">
                <input
                  checked={shouldSaveJob}
                  onChange={(event) => setShouldSaveJob(event.target.checked)}
                  type="checkbox"
                />
                <span>Save job</span>
              </label>
              <button disabled={busyAction !== null} type="submit">
                {busyAction === "create-job"
                  ? shouldSaveJob
                    ? "Saving..."
                    : "Preparing..."
                  : shouldSaveJob
                    ? "Save Job"
                    : "Preview Job"}
              </button>
            </form>

            {job ? (
              <div className="result-block">
                <strong>{job.title ?? "Untitled job"}</strong>
                <span>{job.company ?? job.source_type}</span>
                <p>{job.preview}</p>
                <div className="button-row">
                  <button
                    disabled={busyAction !== null}
                    onClick={handleExtractRequirements}
                    type="button"
                  >
                    {busyAction === "extract-job" ? "Extracting..." : "Extract Requirements"}
                  </button>
                  <button
                    className="secondary-button"
                    disabled={busyAction !== null || !isSavedJob(job)}
                    onClick={handleLoadSavedAnalysis}
                    type="button"
                  >
                    Load Analysis
                  </button>
                </div>
              </div>
            ) : null}
          </section>

          <section className="panel wide">
            <div className="analysis-header">
              <div>
                <h2>Analysis</h2>
                <p>
                  {requirements
                    ? `${requirements.requirements.length} requirements ready`
                    : "No requirements selected"}
                </p>
              </div>
              <button
                disabled={busyAction !== null || !job || !resume || !isSavedJob(job)}
                onClick={handleAnalyze}
                type="button"
              >
                {busyAction === "analyze" ? "Analyzing..." : "Run Analysis"}
              </button>
            </div>

            {analysis ? (
              <div className="analysis-layout">
                <div className="score-panel">
                  <span>Compatibility</span>
                  <strong>{analysis.score}%</strong>
                  <small>
                    {matchSummary.match} match, {matchSummary.partial} partial,{" "}
                    {matchSummary.noMatch} no match
                  </small>
                </div>

                <div className="match-list">
                  {analysis.matches.map((match) => (
                    <article className="match-row" key={match.requirement_id}>
                      <div className="match-main">
                        <span className={`badge ${match.classification.toLowerCase()}`}>
                          {match.classification}
                        </span>
                        <div>
                          <h3>{match.requirement_name}</h3>
                          <span>
                            {match.category} · {match.importance} · {match.confidence}%
                          </span>
                        </div>
                      </div>
                      <p>{match.explanation}</p>
                      <div className="evidence-strip">
                        {match.evidence.map((evidence) => (
                          <span key={evidence.evidence_id}>{evidence.skill}</span>
                        ))}
                      </div>
                    </article>
                  ))}
                </div>
              </div>
            ) : requirements ? (
              <div className="requirements-grid">
                {requirements.requirements.map((requirement) => (
                  <div
                    className="requirement-chip"
                    key={requirement.id ?? `${requirement.name}-${requirement.raw_text}`}
                  >
                    <strong>{requirement.name}</strong>
                    <span>
                      {requirement.category} · {requirement.importance}
                    </span>
                  </div>
                ))}
              </div>
            ) : (
              <div className="empty-state">No analysis loaded</div>
            )}
          </section>

          <aside className="panel side-panel">
            <div className="panel-header">
              <h2>Saved Jobs</h2>
              <span className="pill">{jobs.length} saved</span>
            </div>
            <div className="list compact-list">
              {jobs.map((item) => (
                <div
                  className={`job-list-row ${
                    isSavedJob(job) && job.job_id === item.job_id ? "selected" : ""
                  }`}
                  key={item.job_id}
                >
                  <button className="job-list-button" onClick={() => selectJob(item)} type="button">
                    <strong>{item.title ?? "Untitled job"}</strong>
                    <span>{item.company ?? item.source_type}</span>
                  </button>
                  <button
                    className="danger-button"
                    disabled={busyAction !== null}
                    onClick={() => void handleDeleteJob(item.job_id)}
                    type="button"
                  >
                    {deletingJobId === item.job_id ? "Deleting..." : "Delete"}
                  </button>
                </div>
              ))}
              {jobs.length === 0 ? <div className="empty-state">No saved jobs</div> : null}
            </div>
          </aside>
        </div>
      </section>
    </main>
  );
}

function jobListItemToJob(item: JobListItem): JobImportResponse {
  return {
    job_id: item.job_id,
    source_type: item.source_type,
    url: item.url,
    title: item.title,
    company: item.company,
    scrape_status: item.scrape_status,
    character_count: item.character_count,
    preview: item.preview,
  };
}

function isSavedJob(job: CurrentJob | null | undefined): job is JobImportResponse {
  return Boolean(job && "job_id" in job);
}
