import React, { useState, useEffect, useCallback } from "react";
import { Bell, Search, ArrowLeft, Loader2, Upload, Inbox } from "lucide-react";

const API_BASE = "http://127.0.0.1:8000";

const tokens = `
  @import url('https://fonts.googleapis.com/css2?family=Fraunces:opsz,wght@9..144,400;9..144,500;9..144,600&family=Inter:wght@400;500;600&family=IBM+Plex+Mono:wght@400;500&display=swap');
  .cv-app {
    --ink: #14181C; --paper: #ECEEE8; --surface: #FFFFFF;
    --signal: #2F6F5E; --signal-soft: #DCEAE3;
    --amber: #B4802E; --amber-soft: #F5E9D6;
    --coral: #B4524F; --coral-soft: #F3DEDB;
    --plum: #6B4F84; --plum-soft: #E9E2EF;
    --muted: #67716B; --line: #D9DED3;
    font-family: 'Inter', sans-serif; background: var(--paper); color: var(--ink);
    min-height: 640px; border-radius: 12px; overflow: hidden; display: flex;
  }
  .cv-app * { box-sizing: border-box; }
  .cv-display { font-family: 'Fraunces', serif; }
  .cv-mono { font-family: 'IBM Plex Mono', monospace; }
  .cv-app button { cursor: pointer; font-family: inherit; }
  .cv-nav-item { display: flex; align-items: center; gap: 10px; padding: 10px 14px; border-radius: 8px; font-size: 14px; color: var(--muted); border: none; background: none; width: 100%; text-align: left; }
  .cv-nav-item.active { background: var(--surface); color: var(--ink); font-weight: 500; }
  .cv-card { background: var(--surface); border: 1px solid var(--line); border-radius: 12px; padding: 20px; }
  .cv-btn-primary { background: var(--signal); color: white; border: none; border-radius: 8px; padding: 10px 18px; font-size: 14px; font-weight: 500; }
  .cv-btn-primary:disabled { opacity: 0.5; cursor: not-allowed; }
  .cv-btn-secondary { background: transparent; color: var(--ink); border: 1px solid var(--line); border-radius: 8px; padding: 10px 18px; font-size: 14px; font-weight: 500; }
  .cv-input { width: 100%; padding: 10px 12px; border: 1px solid var(--line); border-radius: 8px; font-size: 14px; font-family: inherit; background: var(--surface); color: var(--ink); }
  .cv-tag { display: inline-block; padding: 4px 10px; border-radius: 20px; font-size: 12px; font-weight: 500; }
  .cv-spin { animation: cv-spin 1s linear infinite; }
  @keyframes cv-spin { from { transform: rotate(0deg); } to { transform: rotate(360deg); } }
  .cv-error { background: var(--coral-soft); color: var(--coral); padding: 10px 14px; border-radius: 8px; font-size: 13px; margin-bottom: 12px; }
`;

async function api(path, { method = "GET", body, token, isFormData = false } = {}) {
  const headers = {};
  if (token) headers["Authorization"] = `Bearer ${token}`;
  if (!isFormData && body) headers["Content-Type"] = "application/json";

  const res = await fetch(`${API_BASE}${path}`, {
    method,
    headers,
    body: isFormData ? body : body ? JSON.stringify(body) : undefined,
  });

  let data = null;
  try { data = await res.json(); } catch (e) { /* no body */ }

  if (!res.ok) {
    const message = data?.detail || `Request failed (${res.status})`;
    throw new Error(typeof message === "string" ? message : JSON.stringify(message));
  }
  return data;
}

function scoreColor(score) {
  if (score >= 75) return { fg: "var(--signal)", bg: "var(--signal-soft)" };
  if (score >= 50) return { fg: "var(--amber)", bg: "var(--amber-soft)" };
  return { fg: "var(--coral)", bg: "var(--coral-soft)" };
}

function MatchDial({ score, size = 64 }) {
  const { fg, bg } = scoreColor(score);
  const stroke = size * 0.1, r = (size - stroke) / 2, c = 2 * Math.PI * r, offset = c - (score / 100) * c;
  return (
    <div style={{ position: "relative", width: size, height: size, flexShrink: 0 }}>
      <svg width={size} height={size} style={{ transform: "rotate(-90deg)" }}>
        <circle cx={size / 2} cy={size / 2} r={r} stroke={bg} strokeWidth={stroke} fill="none" />
        <circle cx={size / 2} cy={size / 2} r={r} stroke={fg} strokeWidth={stroke} fill="none" strokeDasharray={c} strokeDashoffset={offset} strokeLinecap="round" />
      </svg>
      <div className="cv-mono" style={{ position: "absolute", inset: 0, display: "flex", alignItems: "center", justifyContent: "center", fontSize: size * 0.26, fontWeight: 500, color: fg }}>{score}</div>
    </div>
  );
}

function StatusBadge({ status }) {
  const map = { Submitted: { fg: "var(--signal)", bg: "var(--signal-soft)" }, Pending: { fg: "var(--amber)", bg: "var(--amber-soft)" }, "Under Review": { fg: "var(--amber)", bg: "var(--amber-soft)" }, Interview: { fg: "var(--signal)", bg: "var(--signal-soft)" }, Successful: { fg: "var(--signal)", bg: "var(--signal-soft)" }, Unsuccessful: { fg: "var(--coral)", bg: "var(--coral-soft)" } };
  const c = map[status] || map.Pending;
  return <span className="cv-tag" style={{ color: c.fg, background: c.bg }}>{status}</span>;
}

function SourceBadge({ source }) {
  return source === "auto"
    ? <span className="cv-tag" style={{ color: "var(--plum)", background: "var(--plum-soft)" }}>Auto-applied</span>
    : <span className="cv-tag" style={{ color: "var(--muted)", background: "var(--paper)", border: "1px solid var(--line)" }}>Manual</span>;
}

function EmptyState({ icon, title, subtitle, action }) {
  return (
    <div className="cv-card" style={{ textAlign: "center", padding: "48px 24px" }}>
      <div style={{ display: "flex", justifyContent: "center", marginBottom: 14, color: "var(--muted)" }}>{icon}</div>
      <div style={{ fontWeight: 500, fontSize: 15, marginBottom: 4 }}>{title}</div>
      <div style={{ fontSize: 13, color: "var(--muted)", marginBottom: action ? 18 : 0 }}>{subtitle}</div>
      {action}
    </div>
  );
}

function TopBar({ title }) {
  return (
    <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: 20 }}>
      <h1 className="cv-display" style={{ fontSize: 24, fontWeight: 500, margin: 0 }}>{title}</h1>
      <div style={{ background: "var(--surface)", border: "1px solid var(--line)", borderRadius: 8, padding: 8, display: "flex" }}>
        <Bell size={18} color="var(--ink)" />
      </div>
    </div>
  );
}

function Sidebar({ page, setPage, onLogout, userName }) {
  const items = [["overview", "Overview"], ["cv", "CV & skills"], ["matches", "Job matches"], ["skills", "Skill gaps"], ["applications", "Applications"], ["profile", "Profile"]];
  return (
    <div style={{ width: 220, borderRight: "1px solid var(--line)", padding: "20px 14px", display: "flex", flexDirection: "column" }}>
      <div className="cv-display" style={{ fontSize: 19, fontWeight: 600, padding: "0 10px 4px" }}>Smart<span style={{ color: "var(--signal)" }}>CV</span></div>
      <div style={{ fontSize: 12, color: "var(--muted)", padding: "0 10px 20px" }}>{userName}</div>
      <div style={{ display: "flex", flexDirection: "column", gap: 4, flex: 1 }}>
        {items.map(([key, label]) => (
          <button key={key} className={`cv-nav-item ${page === key ? "active" : ""}`} onClick={() => setPage(key)}>{label}</button>
        ))}
      </div>
      <button className="cv-nav-item" onClick={onLogout} style={{ color: "var(--coral)" }}>Log out</button>
    </div>
  );
}

function AuthPage({ onAuthed }) {
  const [mode, setMode] = useState("login");
  const [fullName, setFullName] = useState("");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  const submit = async () => {
    setError("");
    setLoading(true);
    try {
      const path = mode === "login" ? "/api/users/login" : "/api/users/register";
      const body = mode === "login" ? { email, password } : { full_name: fullName, email, password };
      const data = await api(path, { method: "POST", body });
      onAuthed(data.access_token, data.user);
    } catch (e) {
      setError(e.message);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div style={{ flex: 1, display: "flex", alignItems: "center", justifyContent: "center" }}>
      <div className="cv-card" style={{ width: 340 }}>
        <div className="cv-display" style={{ fontSize: 20, fontWeight: 600, marginBottom: 4 }}>Smart<span style={{ color: "var(--signal)" }}>CV</span></div>
        <p style={{ fontSize: 13, color: "var(--muted)", marginBottom: 20 }}>{mode === "login" ? "Log in to see your job matches." : "Create an account to get started."}</p>
        {error && <div className="cv-error">{error}</div>}
        <div style={{ display: "flex", flexDirection: "column", gap: 12, marginBottom: 16 }}>
          {mode === "register" && <input className="cv-input" placeholder="Full name" value={fullName} onChange={(e) => setFullName(e.target.value)} />}
          <input className="cv-input" placeholder="Email" value={email} onChange={(e) => setEmail(e.target.value)} />
          <input className="cv-input" placeholder="Password" type="password" value={password} onChange={(e) => setPassword(e.target.value)} />
        </div>
        <button className="cv-btn-primary" style={{ width: "100%", marginBottom: 12 }} onClick={submit} disabled={loading}>
          {loading ? "Please wait..." : mode === "login" ? "Log in" : "Create account"}
        </button>
        <div style={{ fontSize: 13, textAlign: "center", color: "var(--muted)" }}>
          {mode === "login" ? "New here? " : "Already have an account? "}
          <button style={{ background: "none", border: "none", color: "var(--signal)", fontWeight: 500, padding: 0, fontSize: 13 }} onClick={() => setMode(mode === "login" ? "register" : "login")}>
            {mode === "login" ? "Create one" : "Log in"}
          </button>
        </div>
      </div>
    </div>
  );
}

function Overview({ cvs }) {
  return (
    <div>
      <TopBar title="Welcome back" />
      <div className="cv-card">
        <div style={{ fontWeight: 500, fontSize: 15, marginBottom: 8 }}>Getting started</div>
        <div style={{ fontSize: 14, color: "var(--muted)" }}>
          {cvs.length === 0
            ? "Upload a CV under 'CV & skills' to get your predicted job category, then check 'Job matches' for real, live jobs in that category."
            : `Your CV is predicted as ${cvs[0].predicted_category}. Head to 'Job matches' to see real jobs in that category, already scored for you.`}
        </div>
      </div>
    </div>
  );
}

function CVPage({ token, cvs, refreshCvs }) {
  const [uploading, setUploading] = useState(false);
  const [error, setError] = useState("");

  const handleUpload = async (file) => {
    if (!file) return;
    setUploading(true);
    setError("");
    try {
      const formData = new FormData();
      formData.append("file", file);
      await api("/api/cv/upload", { method: "POST", body: formData, token, isFormData: true });
      await refreshCvs();
    } catch (e) {
      setError(e.message);
    } finally {
      setUploading(false);
    }
  };

  return (
    <div>
      <TopBar title="CV & skills" />
      {error && <div className="cv-error">{error}</div>}

      <div className="cv-card" style={{ marginBottom: 16, textAlign: "center", padding: "32px 20px", border: "1.5px dashed var(--line)" }}>
        {uploading ? (
          <>
            <Loader2 size={28} className="cv-spin" style={{ marginBottom: 14, color: "var(--signal)" }} />
            <div style={{ fontSize: 14, color: "var(--muted)" }}>Uploading and analysing with your trained model...</div>
          </>
        ) : (
          <>
            <div style={{ fontSize: 14, color: "var(--muted)", marginBottom: 12 }}>
              {cvs.length > 0 ? "Upload a new CV to replace your current one" : "Upload a PDF or DOCX CV"}
            </div>
            <input type="file" accept=".pdf,.docx" id="cv-upload-input" style={{ display: "none" }} onChange={(e) => handleUpload(e.target.files[0])} />
            <button className="cv-btn-primary" onClick={() => document.getElementById("cv-upload-input").click()}>
              <Upload size={14} style={{ verticalAlign: "middle", marginRight: 6 }} />Upload CV
            </button>
          </>
        )}
      </div>

      {cvs.length === 0 ? (
        <EmptyState icon={<Upload size={26} />} title="No CV uploaded yet" subtitle="Upload one above to get started." />
      ) : (
        cvs.map((cv) => (
          <div key={cv.id} className="cv-card">
            <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: cv.predicted_category ? 12 : 0 }}>
              <div>
                <div style={{ fontSize: 14, fontWeight: 500 }}>{cv.file_name}</div>
                <div style={{ fontSize: 12, color: "var(--muted)" }}>Uploaded {new Date(cv.upload_date).toLocaleDateString()}</div>
              </div>
              {cv.analysed && <span className="cv-tag" style={{ color: "var(--signal)", background: "var(--signal-soft)" }}>Analysed</span>}
            </div>
            {cv.predicted_category && (
              <div style={{ display: "flex", alignItems: "center", gap: 12, borderTop: "1px solid var(--line)", paddingTop: 12 }}>
                <MatchDial score={Math.round(cv.confidence * 100)} size={44} />
                <div>
                  <div style={{ fontSize: 13, color: "var(--muted)" }}>Predicted category</div>
                  <div style={{ fontWeight: 500, fontSize: 15 }}>{cv.predicted_category}</div>
                </div>
              </div>
            )}
          </div>
        ))
      )}
    </div>
  );
}

function JobCard({ job, applyingId, setApplyingId, token }) {
  const applyToJob = async () => {
    setApplyingId(job.id);
    try {
      await api("/api/applications", {
        method: "POST", token,
        body: { job_id: job.id, job_title: job.title, company: job.company, job_url: job.url, match_score: job.match_score, source: "manual" },
      });
      alert(`Applied to ${job.title}!`);
    } catch (e) {
      alert(e.message);
    } finally {
      setApplyingId(null);
    }
  };

  return (
    <div className="cv-card" style={{ display: "flex", alignItems: "center", gap: 16 }}>
      {job.match_score != null && <MatchDial score={job.match_score} size={56} />}
      <div style={{ flex: 1 }}>
        <div style={{ fontWeight: 500, fontSize: 15 }}>{job.title}</div>
        <div style={{ fontSize: 13, color: "var(--muted)" }}>{job.company} — {job.location}</div>
        {job.auto_applied && (
          <span className="cv-tag" style={{ color: "var(--plum)", background: "var(--plum-soft)", marginTop: 6, display: "inline-block" }}>
            Auto-applied
          </span>
        )}
      </div>
      <a href={job.url} target="_blank" rel="noreferrer" className="cv-btn-secondary" style={{ textDecoration: "none" }}>View</a>
      {!job.auto_applied && (
        <button className="cv-btn-primary" onClick={applyToJob} disabled={applyingId === job.id}>
          {applyingId === job.id ? "..." : "Apply"}
        </button>
      )}
    </div>
  );
}

function MatchesPage({ token, cvs }) {
  const primaryCv = cvs[0];
  const defaultQuery = primaryCv?.predicted_category ? primaryCv.predicted_category.replace(/-/g, " ") : "";

  const [query, setQuery] = useState(defaultQuery);
  const [location, setLocation] = useState("");
  const [jobs, setJobs] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const [applyingId, setApplyingId] = useState(null);
  const [hasSearchedOnce, setHasSearchedOnce] = useState(false);

  const runSearch = useCallback(async (keywords, loc) => {
    setLoading(true);
    setError("");
    try {
      const params = new URLSearchParams({ keywords });
      if (loc) params.append("location", loc);
      if (primaryCv?.id) params.append("cv_id", primaryCv.id);
      const data = await api(`/api/jobs/search?${params}`, { token });
      setJobs(data);
    } catch (e) {
      setError(e.message);
    } finally {
      setLoading(false);
      setHasSearchedOnce(true);
    }
  }, [token, primaryCv]);

  useEffect(() => {
    if (defaultQuery && !hasSearchedOnce) {
      runSearch(defaultQuery, "");
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [defaultQuery]);

  return (
    <div>
      <TopBar title="Job matches" />
      {error && <div className="cv-error">{error}</div>}

      {!primaryCv && (
        <EmptyState icon={<Search size={26} />} title="Upload a CV first" subtitle="Job matches are automatically pulled based on your CV's predicted category." />
      )}

      {primaryCv && (
        <>
          <p style={{ color: "var(--muted)", fontSize: 13, marginBottom: 12 }}>
            Showing jobs for your predicted category: <strong>{primaryCv.predicted_category}</strong>. Want to look at something else?
          </p>
          <div className="cv-card" style={{ marginBottom: 16, display: "flex", gap: 12, alignItems: "center", flexWrap: "wrap" }}>
            <div style={{ position: "relative", flex: 1, minWidth: 180 }}>
              <Search size={15} color="var(--muted)" style={{ position: "absolute", left: 10, top: 12 }} />
              <input className="cv-input" style={{ paddingLeft: 32 }} placeholder="Search a different role" value={query} onChange={(e) => setQuery(e.target.value)} />
            </div>
            <input className="cv-input" style={{ width: 160 }} placeholder="Location (optional)" value={location} onChange={(e) => setLocation(e.target.value)} />
            <button className="cv-btn-primary" onClick={() => runSearch(query, location)} disabled={loading}>{loading ? "Searching..." : "Search"}</button>
          </div>
        </>
      )}

      {loading && <div className="cv-card" style={{ textAlign: "center", padding: 40 }}><Loader2 size={24} className="cv-spin" color="var(--signal)" /></div>}

      {!loading && hasSearchedOnce && jobs.length === 0 && (
        <EmptyState icon={<Search size={26} />} title="No jobs found" subtitle="Try a different search term above." />
      )}

      <div style={{ display: "flex", flexDirection: "column", gap: 12 }}>
        {jobs.map((job) => (
          <JobCard key={job.id} job={job} applyingId={applyingId} setApplyingId={setApplyingId} token={token} />
        ))}
      </div>
    </div>
  );
}

function SkillsPage({ token, cvs }) {
  const primaryCv = cvs[0];
  const [gaps, setGaps] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  const fetchGaps = useCallback(async () => {
    if (!primaryCv?.id) return;
    setLoading(true);
    setError("");
    try {
      const data = await api(`/api/cv/${primaryCv.id}/skill-gaps`, { token });
      setGaps(data);
    } catch (e) {
      setError(e.message);
    } finally {
      setLoading(false);
    }
  }, [primaryCv, token]);

  useEffect(() => { fetchGaps(); }, [fetchGaps]);

  return (
    <div>
      <TopBar title="Skill gaps & learning" />
      {error && <div className="cv-error">{error}</div>}
      {!primaryCv && <EmptyState icon={<Inbox size={26} />} title="Upload a CV first" subtitle="Skill gaps are based on your uploaded CV's predicted category." />}
      {loading && <Loader2 size={24} className="cv-spin" color="var(--signal)" />}
      {gaps && (
        <>
          <p style={{ color: "var(--muted)", fontSize: 14, marginBottom: 16 }}>Based on {gaps.jobs_analysed} real matched jobs for <strong>{gaps.predicted_category}</strong>:</p>
          {gaps.skill_gaps.length === 0 ? (
            <EmptyState icon={<Inbox size={26} />} title="No gaps found" subtitle="Your CV covers what these matched jobs are asking for." />
          ) : (
            <div style={{ display: "flex", flexDirection: "column", gap: 12 }}>
              {gaps.skill_gaps.map((g) => (
                <div key={g.skill} className="cv-card" style={{ display: "flex", alignItems: "center", gap: 16 }}>
                  <span className="cv-tag" style={{ color: "var(--plum)", background: "var(--plum-soft)" }}>{g.skill}</span>
                  <div style={{ flex: 1 }}>
                    <div style={{ fontSize: 13, color: "var(--muted)" }}>Seen in {g.seen_in_jobs} of your matched jobs</div>
                    <div style={{ fontSize: 13 }}>{g.suggestion}</div>
                  </div>
                </div>
              ))}
            </div>
          )}
        </>
      )}
    </div>
  );
}

function ApplicationDetail({ app, onBack }) {
  return (
    <div>
      <button onClick={onBack} className="cv-nav-item" style={{ width: "auto", marginBottom: 16, padding: "6px 10px" }}><ArrowLeft size={15} /> Back</button>
      <div className="cv-card">
        <div style={{ display: "flex", justifyContent: "space-between", marginBottom: 20 }}>
          <div><div className="cv-display" style={{ fontSize: 20, fontWeight: 500 }}>{app.job_title}</div><div style={{ fontSize: 13, color: "var(--muted)" }}>{app.company}</div></div>
          <div style={{ display: "flex", gap: 8 }}><SourceBadge source={app.source} /><StatusBadge status={app.status} /></div>
        </div>
        {app.timeline.map((step, i) => (
          <div key={i} style={{ display: "flex", gap: 12, paddingBottom: 16 }}>
            <div style={{ width: 10, height: 10, borderRadius: "50%", background: step.done ? "var(--signal)" : "var(--line)", marginTop: 4 }} />
            <div><div style={{ fontSize: 14, fontWeight: step.done ? 500 : 400 }}>{step.label}</div><div style={{ fontSize: 12, color: "var(--muted)" }}>{step.date || "Pending"}</div></div>
          </div>
        ))}
      </div>
    </div>
  );
}

function ApplicationsPage({ token }) {
  const [apps, setApps] = useState([]);
  const [loading, setLoading] = useState(true);
  const [selected, setSelected] = useState(null);

  useEffect(() => {
    api("/api/applications", { token }).then(setApps).catch(() => {}).finally(() => setLoading(false));
  }, [token]);

  if (selected) return <ApplicationDetail app={selected} onBack={() => setSelected(null)} />;

  return (
    <div>
      <TopBar title="Applications" />
      {loading && <Loader2 size={24} className="cv-spin" color="var(--signal)" />}
      {!loading && apps.length === 0 && <EmptyState icon={<Inbox size={26} />} title="No applications yet" subtitle="Apply to a job from Job matches and it'll show up here." />}
      {apps.length > 0 && (
        <div className="cv-card">
          {apps.map((app) => (
            <div key={app.id} onClick={() => setSelected(app)} style={{ display: "flex", justifyContent: "space-between", padding: "14px 0", borderTop: "1px solid var(--line)", cursor: "pointer" }}>
              <div><div style={{ fontWeight: 500, fontSize: 14 }}>{app.job_title}</div><div style={{ fontSize: 13, color: "var(--muted)" }}>{app.company}</div></div>
              <div style={{ display: "flex", gap: 8 }}><SourceBadge source={app.source} /><StatusBadge status={app.status} /></div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}

function ProfilePage({ user, token, onUpdated }) {
  const [threshold, setThreshold] = useState(user.minimum_match_score ?? 80);
  const [saving, setSaving] = useState(false);
  const [saved, setSaved] = useState(false);

  const saveThreshold = async () => {
    setSaving(true);
    setSaved(false);
    try {
      const updated = await api("/api/users/profile", {
        method: "PUT", token,
        body: { minimum_match_score: threshold },
      });
      onUpdated(updated);
      setSaved(true);
    } catch (e) {
      alert(e.message);
    } finally {
      setSaving(false);
    }
  };

  return (
    <div>
      <TopBar title="Profile" />
      <div className="cv-card" style={{ maxWidth: 420, marginBottom: 16 }}>
        <div style={{ display: "flex", flexDirection: "column", gap: 14 }}>
          <div><label style={{ fontSize: 12, color: "var(--muted)" }}>Full name</label><input className="cv-input" defaultValue={user.full_name} disabled /></div>
          <div><label style={{ fontSize: 12, color: "var(--muted)" }}>Email</label><input className="cv-input" defaultValue={user.email} disabled /></div>
        </div>
      </div>

      <div className="cv-card" style={{ maxWidth: 420 }}>
        <div style={{ fontWeight: 500, fontSize: 15, marginBottom: 6 }}>Auto-apply threshold</div>
        <div style={{ fontSize: 12, color: "var(--muted)", marginBottom: 14 }}>
          Jobs that score at or above this match percentage get automatically logged as applications — no manual click needed.
        </div>
        <div style={{ display: "flex", alignItems: "center", gap: 10, marginBottom: 14 }}>
          <input type="range" min="50" max="100" value={threshold} onChange={(e) => setThreshold(Number(e.target.value))} style={{ flex: 1 }} />
          <span className="cv-mono" style={{ width: 40, fontSize: 14 }}>{threshold}%</span>
        </div>
        <button className="cv-btn-primary" onClick={saveThreshold} disabled={saving}>
          {saving ? "Saving..." : saved ? "Saved!" : "Save threshold"}
        </button>
      </div>
    </div>
  );
}

export default function SmartCVApp() {
  const [token, setToken] = useState(localStorage.getItem("cv_token") || "");
  const [user, setUser] = useState(null);
  const [page, setPage] = useState("overview");
  const [cvs, setCvs] = useState([]);

  const refreshCvs = useCallback(async () => {
    if (!token) return;
    try {
      const data = await api("/api/cv", { token });
      setCvs(data);
    } catch (e) { /* token may be stale */ }
  }, [token]);

  useEffect(() => { refreshCvs(); }, [refreshCvs]);

  const handleAuthed = (newToken, newUser) => {
    localStorage.setItem("cv_token", newToken);
    setToken(newToken);
    setUser(newUser);
  };

  const handleLogout = () => {
    localStorage.removeItem("cv_token");
    setToken("");
    setUser(null);
    setCvs([]);
  };

  const pages = {
    overview: <Overview cvs={cvs} />,
    cv: <CVPage token={token} cvs={cvs} refreshCvs={refreshCvs} />,
    matches: <MatchesPage token={token} cvs={cvs} />,
    skills: <SkillsPage token={token} cvs={cvs} />,
    applications: <ApplicationsPage token={token} />,
    profile: user ? <ProfilePage user={user} token={token} onUpdated={setUser} /> : null,
  };

  return (
    <div className="cv-app">
      <style>{tokens}</style>
      {!token ? (
        <AuthPage onAuthed={handleAuthed} />
      ) : (
        <>
          <Sidebar page={page} setPage={setPage} onLogout={handleLogout} userName={user?.full_name || "Signed in"} />
          <div style={{ flex: 1, padding: "28px 32px", overflowY: "auto" }}>
            {pages[page]}
          </div>
        </>
      )}
    </div>
  );
}
