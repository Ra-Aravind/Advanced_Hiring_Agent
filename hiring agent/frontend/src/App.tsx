import {
  BrowserRouter, Routes, Route, Navigate, useNavigate, useParams,
} from 'react-router-dom';
import { useState, useEffect, useCallback, useRef } from 'react';
import {
  Bot, Lock, Mail, AlertCircle, Loader, ChevronLeft, ChevronRight,
  Clock, CheckCircle, XCircle, Plus, Search, BarChart2, BookOpen,
  ClipboardList, LogOut, User, Star, TrendingUp, Award, Zap, Send,
  Copy, RefreshCw, KeyRound, Users, ArrowRight, Eye, Trash2, Filter,
  ShieldCheck, Code2, FileQuestion, ChevronDown, CheckCheck, Trophy,
  Briefcase, Calendar, Video, UserCheck, MessageSquare, ExternalLink,
} from 'lucide-react';

// ─── API ─────────────────────────────────────────────────────────
const API = '/api';
const tok = () => localStorage.getItem('token') ?? '';

async function get(path: string) {
  const r = await fetch(`${API}${path}`, { headers: { Authorization: `Bearer ${tok()}` } });
  const d = await r.json();
  if (!r.ok) throw new Error(d.detail || 'Request failed');
  return d;
}
async function post(path: string, body: object) {
  const r = await fetch(`${API}${path}`, {
    method: 'POST', headers: { 'Content-Type': 'application/json', Authorization: `Bearer ${tok()}` },
    body: JSON.stringify(body),
  });
  const d = await r.json();
  if (!r.ok) throw new Error(d.detail || 'Request failed');
  return d;
}
async function put(path: string, body: object) {
  const r = await fetch(`${API}${path}`, {
    method: 'PUT', headers: { 'Content-Type': 'application/json', Authorization: `Bearer ${tok()}` },
    body: JSON.stringify(body),
  });
  const d = await r.json();
  if (!r.ok) throw new Error(d.detail || 'Request failed');
  return d;
}
async function del(path: string) {
  const r = await fetch(`${API}${path}`, { method: 'DELETE', headers: { Authorization: `Bearer ${tok()}` } });
  if (r.status === 204) return null;
  const d = await r.json();
  if (!r.ok) throw new Error(d.detail || 'Request failed');
  return d;
}

// ─── Types ────────────────────────────────────────────────────────
interface Tech { id: string; name: string; slug: string; icon?: string; color?: string; }
interface DiffMix { beginner: number; intermediate: number; advanced: number; }
interface Assessment {
  id: string; title: string; technology_id: string; technology_name: string; technology_icon: string;
  difficulty_mix: DiffMix; total_questions: number; duration_minutes: number; passing_score: number;
  instructions?: string; is_active: boolean; created_at: string; session_count: number; access_code?: string;
}
interface Session {
  id: string; config_id: string; candidate_name?: string;
  candidate_email?: string; status: string; started_at?: string; submitted_at?: string;
  expires_at?: string; created_at: string; assessment_title?: string; technology_name?: string;
  duration_minutes?: number; total_questions?: number;
  score?: number; percentage?: number;
}
interface Result {
  id: string; session_id: string; candidate_name?: string; candidate_email?: string;
  assessment_title?: string; technology_name?: string;
  total_score: number; max_possible_score: number; percentage: number; passed: boolean;
  shortlisted?: boolean; per_question_scores?: PQScore[];
  strengths?: string[]; weaknesses?: string[]; ai_feedback?: string; evaluated_at: string;
}
interface PQScore {
  question_text: string; question_type: string; candidate_answer?: string;
  correct_answer?: string; score: number; max_score: number; is_correct: boolean; ai_feedback?: string;
}
interface SessionInfo {
  access_code: string; status: string; assessment_title: string; technology: string;
  technology_icon: string; total_questions: number; duration_minutes: number;
  passing_score: number; instructions: string; candidate_name?: string; candidate_email?: string;
}
interface CandidateQ {
  id: string; question_text: string; question_type: string; difficulty: string;
  max_score: number; options?: { label: string; text: string }[];
}

// ─── Shared helpers ───────────────────────────────────────────────
function Spin() { return <Loader size={16} style={{ animation: 'spin 1s linear infinite', display:'inline-block' }} />; }

function Err({ msg }: { msg: string }) {
  return (
    <div style={{
      background: 'rgba(239,68,68,0.12)', border: '1px solid rgba(239,68,68,0.3)',
      borderRadius: '10px', padding: '0.75rem 1rem',
      display: 'flex', alignItems: 'flex-start', gap: '0.6rem', color: '#f87171',
      marginBottom: '1rem', fontSize: '0.875rem', lineHeight: 1.5,
    }}>
      <AlertCircle size={15} style={{ flexShrink: 0, marginTop: '2px' }} />{msg}
    </div>
  );
}

function Badge({ children, color }: { children: React.ReactNode; color: string }) {
  return (
    <span className="badge" style={{ background: `${color}20`, color, border: `1px solid ${color}40` }}>
      {children}
    </span>
  );
}

function CopyBtn({ text }: { text: string }) {
  const [copied, setCopied] = useState(false);
  const copy = () => {
    navigator.clipboard.writeText(text);
    setCopied(true);
    setTimeout(() => setCopied(false), 1800);
  };
  return (
    <button className="btn-icon" onClick={copy} title="Copy code">
      {copied ? <CheckCheck size={14} color="#10b981" /> : <Copy size={14} />}
    </button>
  );
}

function StatusBadge({ status }: { status: string }) {
  const map: Record<string, [string, string]> = {
    pending: ['#f59e0b', '⏳ Pending'],
    in_progress: ['#6366f1', '⚡ In Progress'],
    submitted: ['#06b6d4', '📩 Submitted'],
    evaluated: ['#10b981', '✅ Evaluated'],
  };
  const [color, label] = map[status] ?? ['#64748b', status];
  return <Badge color={color}>{label}</Badge>;
}

const diffColor = (d: string) => d === 'beginner' ? '#10b981' : d === 'intermediate' ? '#f59e0b' : '#ef4444';
const typeColor = (t: string) => t === 'mcq' ? '#6366f1' : t === 'true_false' ? '#8b5cf6' : '#06b6d4';

// ─────────────────────────────────────────────────────────────────
// LANDING PAGE – Tabbed Recruiter / Interviewer / Candidate
// ─────────────────────────────────────────────────────────────────
function LandingPage() {
  const navigate = useNavigate();
  const [tab, setTab] = useState<'recruiter' | 'interviewer' | 'candidate'>('recruiter');

  // Recruiter login state (Phase 1 admin)
  const [email, setEmail] = useState('admin@company.com');
  const [password, setPassword] = useState('');
  const [loginLoading, setLoginLoading] = useState(false);
  const [loginErr, setLoginErr] = useState('');

  // Interviewer login state (Phase 2)
  const [intvEmail, setIntvEmail] = useState('rahul.sharma@hiringco.com');
  const [intvPassword, setIntvPassword] = useState('');
  const [intvLoading, setIntvLoading] = useState(false);
  const [intvErr, setIntvErr] = useState('');

  // Candidate state
  const [code, setCode] = useState('');
  const [codeLoading, setCodeLoading] = useState(false);
  const [codeErr, setCodeErr] = useState('');

  const handleLogin = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoginErr(''); setLoginLoading(true);
    try {
      const data = await post('/auth/login', { email, password });
      localStorage.setItem('token', data.access_token);
      localStorage.setItem('user', JSON.stringify(data.user));
      navigate('/recruiter/dashboard');
    } catch (e: any) { setLoginErr(e.message); }
    finally { setLoginLoading(false); }
  };

  const handleInterviewerLogin = async (e: React.FormEvent) => {
    e.preventDefault();
    setIntvErr(''); setIntvLoading(true);
    try {
      const r = await fetch('http://127.0.0.1:8000/api/v1/auth/login', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ email: intvEmail, password: intvPassword }),
      });
      const data = await r.json();
      if (!r.ok) throw new Error(data.detail || 'Invalid credentials');
      if (data.role !== 'INTERVIEWER' && data.role !== 'RECRUITER') {
        throw new Error('This portal is for interviewers only.');
      }
      // Store Phase 2 user in sessionStorage so Phase2Dashboard can read it
      sessionStorage.setItem('p2user', JSON.stringify(data));
      navigate('/interviewer/dashboard');
    } catch (e: any) { setIntvErr(e.message); }
    finally { setIntvLoading(false); }
  };

  const handleCodeSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setCodeErr(''); setCodeLoading(true);
    try {
      const clean = code.trim().toUpperCase();
      if (!clean) { setCodeErr('Please enter your access code.'); return; }
      const r = await fetch(`${API}/candidate/config/${clean}`);
      const d = await r.json();
      if (!r.ok) throw new Error(d.detail || 'Invalid access code.');
      navigate(`/candidate/${clean}`);
    } catch (e: any) { setCodeErr(e.message); }
    finally { setCodeLoading(false); }
  };

  const clearErrors = () => { setLoginErr(''); setCodeErr(''); setIntvErr(''); };

  return (
    <div className="animate-fade-in" style={{ minHeight: 'calc(100vh - 64px)', display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center', padding: '2rem 1rem' }}>
      {/* Hero */}
      <div style={{ textAlign: 'center', marginBottom: '2.5rem' }}>
        <div style={{ display: 'inline-flex', alignItems: 'center', gap: '0.5rem', background: 'rgba(99,102,241,0.12)', border: '1px solid rgba(99,102,241,0.25)', color: '#a5b4fc', padding: '0.35rem 1rem', borderRadius: '999px', fontSize: '0.8rem', fontWeight: 600, marginBottom: '1.25rem' }}>
          <Zap size={13} /> AI-Powered Technical Assessments & Interview Management
        </div>
        <h1 style={{ fontSize: 'clamp(2rem, 5vw, 3rem)', fontWeight: 900, letterSpacing: '-0.04em', lineHeight: 1.1, marginBottom: '0.75rem' }}>
          Hire Smarter,<br />
          <span style={{ background: 'linear-gradient(135deg, #6366f1, #8b5cf6, #10b981)', WebkitBackgroundClip: 'text', WebkitTextFillColor: 'transparent', backgroundClip: 'text' }}>
            Score Instantly
          </span>
        </h1>
        <p style={{ color: 'var(--text-muted)', fontSize: '1rem', maxWidth: '480px', margin: '0 auto', lineHeight: 1.6 }}>
          Create technical assessments, schedule interviews with AI-generated meeting links, and let AI evaluate your candidates automatically.
        </p>
      </div>

      {/* Card */}
      <div className="glass-panel" style={{ width: '100%', maxWidth: '480px', padding: '1.75rem' }}>
        {/* Tabs */}
        <div className="tab-bar" style={{ marginBottom: '1.75rem', display: 'grid', gridTemplateColumns: '1fr 1fr 1fr' }}>
          <button className={`tab-btn ${tab === 'recruiter' ? 'active' : ''}`} onClick={() => { setTab('recruiter'); clearErrors(); }}>
            <ShieldCheck size={14} /> Recruiter
          </button>
          <button className={`tab-btn ${tab === 'interviewer' ? 'active' : ''}`} onClick={() => { setTab('interviewer'); clearErrors(); }}
            style={tab === 'interviewer' ? { background: 'rgba(139,92,246,0.15)', color: '#c4b5fd', borderColor: 'rgba(139,92,246,0.35)' } : {}}>
            <Briefcase size={14} /> Interviewer
          </button>
          <button className={`tab-btn ${tab === 'candidate' ? 'active-green' : ''}`} onClick={() => { setTab('candidate'); clearErrors(); }}>
            <User size={14} /> Candidate
          </button>
        </div>

        {/* ── RECRUITER TAB ── */}
        {tab === 'recruiter' && (
          <div className="animate-fade-in">
            <h2 style={{ fontSize: '1.15rem', fontWeight: 700, marginBottom: '0.25rem' }}>Recruiter Sign In</h2>
            <p style={{ color: 'var(--text-muted)', fontSize: '0.825rem', marginBottom: '1.5rem' }}>
              Manage assessments, generate codes &amp; review results.
            </p>
            {loginErr && <Err msg={loginErr} />}
            <form onSubmit={handleLogin}>
              <div className="form-group">
                <label className="form-label"><Mail size={12} style={{ display: 'inline', marginRight: '4px' }} />Email</label>
                <input id="recruiter-email" type="email" className="form-input" value={email}
                  onChange={e => setEmail(e.target.value)} placeholder="admin@company.com" required />
              </div>
              <div className="form-group">
                <label className="form-label"><Lock size={12} style={{ display: 'inline', marginRight: '4px' }} />Password</label>
                <input id="recruiter-password" type="password" className="form-input" value={password}
                  onChange={e => setPassword(e.target.value)} placeholder="Enter password" required />
              </div>
              <button id="recruiter-login-btn" type="submit" className="btn-primary" disabled={loginLoading}
                style={{ width: '100%', padding: '0.875rem', display: 'flex', alignItems: 'center', justifyContent: 'center', gap: '0.5rem', fontSize: '0.95rem' }}>
                {loginLoading ? <><Spin /> Signing in...</> : <>Sign In <ArrowRight size={16} /></>}
              </button>
              <p style={{ textAlign: 'center', marginTop: '1rem', fontSize: '0.75rem', color: 'var(--text-muted)' }}>
                Default: <code style={{ color: 'var(--text-main)', background: 'rgba(255,255,255,0.07)', padding: '1px 6px', borderRadius: '4px' }}>Admin@123</code>
              </p>
            </form>
          </div>
        )}

        {/* ── INTERVIEWER TAB ── */}
        {tab === 'interviewer' && (
          <div className="animate-fade-in">
            <h2 style={{ fontSize: '1.15rem', fontWeight: 700, marginBottom: '0.25rem' }}>Interviewer Sign In</h2>
            <p style={{ color: 'var(--text-muted)', fontSize: '0.825rem', marginBottom: '1.5rem' }}>
              Access your interview schedule, candidate profiles &amp; submit evaluations.
            </p>
            {intvErr && <Err msg={intvErr} />}
            <form onSubmit={handleInterviewerLogin}>
              <div className="form-group">
                <label className="form-label"><Mail size={12} style={{ display: 'inline', marginRight: '4px' }} />Email</label>
                <input type="email" className="form-input" value={intvEmail}
                  onChange={e => setIntvEmail(e.target.value)} placeholder="interviewer@company.com" required />
              </div>
              <div className="form-group">
                <label className="form-label"><Lock size={12} style={{ display: 'inline', marginRight: '4px' }} />Password</label>
                <input type="password" className="form-input" value={intvPassword}
                  onChange={e => setIntvPassword(e.target.value)} placeholder="Enter password" required />
              </div>
              <button type="submit" disabled={intvLoading}
                style={{ width: '100%', padding: '0.875rem', display: 'flex', alignItems: 'center', justifyContent: 'center', gap: '0.5rem', fontSize: '0.95rem', background: 'linear-gradient(135deg,#7c3aed,#6d28d9)', color: 'white', border: 'none', borderRadius: '10px', cursor: intvLoading ? 'wait' : 'pointer', fontWeight: 600 }}>
                {intvLoading ? <><Spin /> Signing in...</> : <>Sign In <ArrowRight size={16} /></>}
              </button>
              <div style={{ marginTop: '1rem', padding: '0.75rem', background: 'rgba(139,92,246,0.08)', borderRadius: '8px', border: '1px solid rgba(139,92,246,0.2)' }}>
                <p style={{ fontSize: '0.72rem', color: 'var(--text-muted)', marginBottom: '0.25rem', fontWeight: 600 }}>Demo accounts (password: password123)</p>
                {['rahul.sharma', 'priya.patel', 'arun.kumar', 'divya.menon'].map(n => (
                  <p key={n} style={{ fontSize: '0.72rem', color: '#a5b4fc', cursor: 'pointer', margin: '0.1rem 0' }}
                    onClick={() => setIntvEmail(`${n}@hiringco.com`)}>
                    → {n}@hiringco.com
                  </p>
                ))}
              </div>
            </form>
          </div>
        )}

        {/* ── CANDIDATE TAB ── */}
        {tab === 'candidate' && (
          <div className="animate-fade-in">
            <h2 style={{ fontSize: '1.15rem', fontWeight: 700, marginBottom: '0.25rem' }}>Join Your Assessment</h2>
            <p style={{ color: 'var(--text-muted)', fontSize: '0.825rem', marginBottom: '1.5rem' }}>
              Enter the access code provided by your recruiter to begin.
            </p>
            {codeErr && <Err msg={codeErr} />}
            <form onSubmit={handleCodeSubmit}>
              <div className="form-group">
                <label className="form-label"><KeyRound size={12} style={{ display: 'inline', marginRight: '4px' }} />Access Code</label>
                <input id="access-code-input" type="text" className="form-input"
                  value={code} onChange={e => setCode(e.target.value.toUpperCase())}
                  placeholder="e.g. AB-CDE123" maxLength={12}
                  style={{ textAlign: 'center', fontSize: '1.5rem', fontFamily: 'var(--font-mono)', letterSpacing: '6px', fontWeight: 700 }}
                  required />
              </div>
              <button id="candidate-enter-btn" type="submit" className="btn-green" disabled={codeLoading}
                style={{ width: '100%', padding: '0.875rem', display: 'flex', alignItems: 'center', justifyContent: 'center', gap: '0.5rem', fontSize: '0.95rem' }}>
                {codeLoading ? <><Spin /> Validating...</> : <>Start Assessment <ArrowRight size={16} /></>}
              </button>
            </form>
          </div>
        )}
      </div>

      {/* Feature pills */}
      <div style={{ display: 'flex', gap: '0.75rem', marginTop: '2rem', flexWrap: 'wrap', justifyContent: 'center' }}>
        {[['🤖', 'AI Evaluation'], ['⚡', 'Instant Results'], ['🔐', 'Secure Codes'], ['📊', 'Detailed Analytics'], ['📅', 'Interview Scheduling'], ['🎥', 'Jitsi Meetings']].map(([icon, label]) => (
          <div key={label} style={{ display: 'flex', alignItems: 'center', gap: '0.35rem', padding: '0.35rem 0.9rem', background: 'rgba(255,255,255,0.04)', border: '1px solid var(--glass-border)', borderRadius: '999px', fontSize: '0.78rem', color: 'var(--text-muted)' }}>
            {icon} {label}
          </div>
        ))}
      </div>
    </div>
  );
}



// ─────────────────────────────────────────────────────────────────
// RECRUITER NAVBAR (shared for all recruiter pages)
// ─────────────────────────────────────────────────────────────────
function RecruiterNav({ active }: { active: string }) {
  const navigate = useNavigate();
  const user = JSON.parse(localStorage.getItem('user') ?? '{}');
  const handleLogout = () => { localStorage.clear(); navigate('/'); };
  const links = [
    { path: '/recruiter/dashboard', label: 'Dashboard' },
    { path: '/recruiter/create', label: 'New Assessment' },
    { path: '/recruiter/assessments', label: 'All Assessments' },
    { path: '/recruiter/interviews', label: 'Interview Management' },
  ];
  return (
    <nav className="navbar">
      <div className="brand" onClick={() => navigate('/recruiter/dashboard')} style={{ cursor: 'pointer' }}>
        <Bot className="brand-icon" size={22} />
        <span>AI Assessor</span>
      </div>
      <div className="nav-links">
        {links.map(l => (
          <a key={l.path} href={l.path} className={`nav-link ${active === l.path ? 'active' : ''}`}
            onClick={e => { e.preventDefault(); navigate(l.path); }}>
            {l.label}
          </a>
        ))}
        <div style={{ width: '1px', height: '20px', background: 'var(--glass-border)', margin: '0 0.25rem' }} />
        <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', padding: '0.35rem 0.75rem', background: 'rgba(255,255,255,0.05)', borderRadius: '8px' }}>
          <div style={{ width: '26px', height: '26px', borderRadius: '50%', background: 'linear-gradient(135deg,#6366f1,#8b5cf6)', display: 'flex', alignItems: 'center', justifyContent: 'center', fontSize: '0.7rem', fontWeight: 700 }}>
            {user.full_name?.charAt(0) ?? 'A'}
          </div>
          <span style={{ fontSize: '0.8rem', fontWeight: 500 }}>{user.full_name?.split(' ')[0] ?? 'Admin'}</span>
          <button className="btn-icon" onClick={handleLogout} title="Logout" style={{ marginLeft: '0.25rem', padding: '0.25rem' }}>
            <LogOut size={13} />
          </button>
        </div>
      </div>
    </nav>
  );
}

// ─────────────────────────────────────────────────────────────────
// RECRUITER DASHBOARD
// ─────────────────────────────────────────────────────────────────
function RecruiterDashboard() {
  const navigate = useNavigate();
  const [analytics, setAnalytics] = useState<any>(null);
  const [assessments, setAssessments] = useState<Assessment[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    Promise.all([
      get('/admin/results/analytics/summary').catch(() => null),
      get('/admin/assessments').catch(() => []),
    ]).then(([a, b]) => { setAnalytics(a); setAssessments(b || []); setLoading(false); });
  }, []);

  const stats = analytics ? [
    { label: 'Assessments', value: analytics.total_assessments, icon: <ClipboardList size={18} />, color: '#6366f1' },
    { label: 'Candidates', value: analytics.total_candidates, icon: <Users size={18} />, color: '#10b981' },
    { label: 'Pass Rate', value: `${analytics.pass_rate}%`, icon: <TrendingUp size={18} />, color: '#f59e0b' },
    { label: 'Avg Score', value: `${analytics.avg_score}%`, icon: <Award size={18} />, color: '#ec4899' },
  ] : [];

  return (
    <>
      <RecruiterNav active="/recruiter/dashboard" />
      <div className="animate-fade-in" style={{ maxWidth: '1100px', margin: '0 auto', padding: '2rem 1.5rem' }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: '2rem', flexWrap: 'wrap', gap: '1rem' }}>
          <div>
            <h1 style={{ fontSize: '1.6rem', fontWeight: 800, letterSpacing: '-0.03em' }}>Dashboard</h1>
            <p style={{ color: 'var(--text-muted)', marginTop: '0.25rem', fontSize: '0.875rem' }}>Overview of your technical assessments</p>
          </div>
          <button className="btn-primary" onClick={() => navigate('/recruiter/create')}
            style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
            <Plus size={16} /> Create Assessment
          </button>
        </div>

        {/* Stats */}
        {analytics && (
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(200px,1fr))', gap: '1rem', marginBottom: '2rem' }}>
            {stats.map(s => (
              <div key={s.label} className="glass-panel stat-card">
                <div className="stat-icon" style={{ background: `${s.color}18`, color: s.color }}>{s.icon}</div>
                <div>
                  <div className="stat-value">{s.value}</div>
                  <div className="stat-label">{s.label}</div>
                </div>
              </div>
            ))}
          </div>
        )}

        {/* Assessments list */}
        <div className="glass-panel" style={{ overflow: 'hidden' }}>
          <div style={{ padding: '1.1rem 1.5rem', borderBottom: '1px solid var(--glass-border)', display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
            <h2 style={{ fontWeight: 700, fontSize: '1rem' }}>Your Assessments</h2>
            <button className="btn-secondary" style={{ fontSize: '0.8rem', padding: '0.4rem 0.875rem' }} onClick={() => navigate('/recruiter/assessments')}>
              View All
            </button>
          </div>
          {loading ? (
            <div style={{ padding: '3rem', textAlign: 'center', color: 'var(--text-muted)' }}><Spin /></div>
          ) : assessments.length === 0 ? (
            <div style={{ padding: '3rem', textAlign: 'center', color: 'var(--text-muted)' }}>
              <ClipboardList size={40} style={{ opacity: 0.3, marginBottom: '0.75rem' }} />
              <p>No assessments yet.</p>
              <button className="btn-primary" onClick={() => navigate('/recruiter/create')} style={{ marginTop: '1rem', display: 'inline-flex', alignItems: 'center', gap: '0.4rem' }}>
                <Plus size={15} /> Create your first
              </button>
            </div>
          ) : (
            assessments.slice(0, 6).map(a => (
              <div key={a.id} className="assessment-card" onClick={() => navigate(`/recruiter/assessment/${a.id}`)}>
                <div style={{ fontSize: '1.5rem', flexShrink: 0 }}>{a.technology_icon}</div>
                <div style={{ flex: 1, minWidth: 0 }}>
                  <div style={{ fontWeight: 600, marginBottom: '0.2rem', whiteSpace: 'nowrap', overflow: 'hidden', textOverflow: 'ellipsis' }}>{a.title}</div>
                  <div style={{ display: 'flex', gap: '0.5rem', flexWrap: 'wrap', alignItems: 'center' }}>
                    <Badge color="#6366f1">{a.technology_name}</Badge>
                    <Badge color="#94a3b8">{a.total_questions} Qs · {a.duration_minutes}min</Badge>
                    <Badge color="#f59e0b">Pass {a.passing_score}%</Badge>
                  </div>
                </div>
                <div style={{ textAlign: 'right', flexShrink: 0 }}>
                  <div style={{ fontWeight: 700, fontSize: '1.3rem', color: '#6366f1' }}>{a.session_count}</div>
                  <div style={{ fontSize: '0.7rem', color: 'var(--text-muted)' }}>candidates</div>
                </div>
                <ArrowRight size={16} color="var(--text-muted)" />
              </div>
            ))
          )}
        </div>
      </div>
    </>
  );
}

// ─────────────────────────────────────────────────────────────────
// CREATE ASSESSMENT (AI Command + Form + Code Generation)
// ─────────────────────────────────────────────────────────────────
function CreateAssessment() {
  const navigate = useNavigate();
  const [step, setStep] = useState(1); // 1=config, 2=codes
  const [techs, setTechs] = useState<Tech[]>([]);
  const [command, setCommand] = useState('');
  const [parsing, setParsing] = useState(false);
  const [parseOk, setParseOk] = useState(false);

  const [title, setTitle] = useState('');
  const [techId, setTechId] = useState('');
  const [totalQ, setTotalQ] = useState(10);
  const [beg, setBeg] = useState(3);
  const [inter, setInter] = useState(5);
  const [adv, setAdv] = useState(2);
  const [duration, setDuration] = useState(60);
  const [passing, setPassing] = useState(60);
  const [instructions, setInstructions] = useState('');

  const [creating, setCreating] = useState(false);
  const [createErr, setCreateErr] = useState('');
  const [generatedAssessment, setGeneratedAssessment] = useState<Assessment | null>(null);
  const [copiedIdx, setCopiedIdx] = useState<boolean>(false);

  useEffect(() => {
    get('/admin/questions/technologies/list').then(setTechs).catch(() => {});
  }, []);

  const handleParse = async () => {
    if (!command.trim()) return;
    setParsing(true); setParseOk(false);
    try {
      const r = await post('/admin/assessments/agent/parse', { command });
      if (r.success && r.parsed_config) {
        const c = r.parsed_config;
        setTitle(c.title || '');
        setTotalQ(c.total_questions || 10);
        setBeg(c.difficulty_mix?.beginner ?? 0);
        setInter(c.difficulty_mix?.intermediate ?? 0);
        setAdv(c.difficulty_mix?.advanced ?? 0);
        setDuration(c.duration_minutes || 60);
        setPassing(c.passing_score || 60);
        setInstructions(c.instructions || '');
        const t = techs.find(t => t.name.toLowerCase() === (c.technology || '').toLowerCase());
        if (t) setTechId(t.id);
        setParseOk(true);
      }
    } catch { }
    setParsing(false);
  };

  const handleCreate = async (e: React.FormEvent) => {
    e.preventDefault();
    setCreateErr(''); setCreating(true);
    try {
      const a: Assessment = await post('/admin/assessments', {
        title, technology_id: techId,
        total_questions: totalQ,
        difficulty_mix: { beginner: beg, intermediate: inter, advanced: adv },
        duration_minutes: duration, passing_score: passing, instructions,
        original_command: command || null,
      });
      setGeneratedAssessment(a);
      setStep(2);
    } catch (e: any) { setCreateErr(e.message); }
    setCreating(false);
  };

  const copyCode = (code: string) => {
    navigator.clipboard.writeText(code);
    setCopiedIdx(true);
    setTimeout(() => setCopiedIdx(false), 2000);
  };

  const inpStyle = {
    background: 'rgba(8,14,26,0.6)', border: '1px solid var(--glass-border)',
    color: 'var(--text-main)', padding: '0.65rem 0.9rem',
    borderRadius: '10px', fontSize: '0.875rem', width: '100%',
  } as React.CSSProperties;

  const mixOk = beg + inter + adv === totalQ;

  return (
    <>
      <RecruiterNav active="/recruiter/create" />
      <div className="animate-fade-in" style={{ maxWidth: '780px', margin: '0 auto', padding: '2rem 1.5rem' }}>
        {/* Back + Title */}
        <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem', marginBottom: '1.75rem' }}>
          <button className="btn-icon" onClick={() => navigate('/recruiter/dashboard')}><ChevronLeft size={18} /></button>
          <div>
            <h1 style={{ fontSize: '1.5rem', fontWeight: 800, letterSpacing: '-0.03em' }}>
              {step === 1 ? 'Create Assessment' : '🎉 Assessment Created!'}
            </h1>
            <p style={{ color: 'var(--text-muted)', fontSize: '0.825rem' }}>
              {step === 1 ? 'Use AI or configure manually — then generate access codes' : 'Generate access codes to share with candidates'}
            </p>
          </div>
        </div>

        {/* Steps indicator */}
        <div className="step-indicator" style={{ marginBottom: '2rem' }}>
          {['Configure', 'Generate Codes'].map((s, i) => (
            <>
              <div key={s} className={`step-dot ${step > i + 1 ? 'done' : step === i + 1 ? 'active' : 'pending'}`}>
                {step > i + 1 ? <CheckCircle size={14} /> : i + 1}
              </div>
              <span style={{ fontSize: '0.75rem', color: step === i + 1 ? 'var(--text-main)' : 'var(--text-muted)', margin: '0 0.5rem', whiteSpace: 'nowrap' }}>{s}</span>
              {i < 1 && <div className="step-line" style={{ background: step > 1 ? 'var(--secondary)' : 'var(--glass-border)', transition: 'background 0.4s' }} />}
            </>
          ))}
        </div>

        {step === 1 && (
          <>
            {/* AI Command Parser */}
            <div className="glass-panel" style={{ padding: '1.5rem', marginBottom: '1.5rem', borderTop: '3px solid var(--primary)' }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', marginBottom: '0.5rem' }}>
                <Zap size={16} color="var(--primary)" />
                <h2 style={{ fontWeight: 700, fontSize: '0.95rem' }}>AI Command Parser <span style={{ color: 'var(--text-muted)', fontWeight: 400, fontSize: '0.8rem' }}>(optional)</span></h2>
              </div>
              <p style={{ color: 'var(--text-muted)', fontSize: '0.8rem', marginBottom: '1rem', lineHeight: 1.5 }}>
                Describe your assessment in plain English and AI will fill the form below.
              </p>
              <div style={{ display: 'flex', gap: '0.75rem' }}>
                <input value={command} onChange={e => setCommand(e.target.value)}
                  placeholder='e.g. "Create a Python test with 15 intermediate questions, 90 min, 70% passing"'
                  style={{ ...inpStyle, flex: 1 }}
                  onKeyDown={e => e.key === 'Enter' && handleParse()} />
                <button onClick={handleParse} disabled={parsing || !command.trim()} className="btn-primary"
                  style={{ display: 'flex', alignItems: 'center', gap: '0.4rem', whiteSpace: 'nowrap', padding: '0.65rem 1.1rem' }}>
                  {parsing ? <><Spin />Parsing...</> : <><Zap size={14} />Parse</>}
                </button>
              </div>
              {parseOk && <div style={{ marginTop: '0.6rem', padding: '0.6rem 0.875rem', background: 'rgba(16,185,129,0.1)', border: '1px solid rgba(16,185,129,0.25)', borderRadius: '8px', fontSize: '0.8rem', color: '#34d399', display: 'flex', alignItems: 'center', gap: '0.4rem' }}>
                <CheckCircle size={13} /> Form auto-filled! Review and adjust below.
              </div>}
            </div>

            {/* Config Form */}
            <form className="glass-panel" style={{ padding: '1.75rem' }} onSubmit={handleCreate}>
              <h2 style={{ fontWeight: 700, fontSize: '0.95rem', marginBottom: '1.25rem' }}>Assessment Configuration</h2>
              {createErr && <Err msg={createErr} />}

              <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '1rem', marginBottom: '1rem' }}>
                <div>
                  <label style={{ display: 'block', fontSize: '0.75rem', color: 'var(--text-muted)', marginBottom: '0.35rem', fontWeight: 600, textTransform: 'uppercase', letterSpacing: '0.04em' }}>Title *</label>
                  <input value={title} onChange={e => setTitle(e.target.value)} required style={inpStyle} placeholder="e.g. Python Developer – Round 1" />
                </div>
                <div>
                  <label style={{ display: 'block', fontSize: '0.75rem', color: 'var(--text-muted)', marginBottom: '0.35rem', fontWeight: 600, textTransform: 'uppercase', letterSpacing: '0.04em' }}>Technology *</label>
                  <select value={techId} onChange={e => setTechId(e.target.value)} required style={{ ...inpStyle, cursor: 'pointer' }}>
                    <option value="">Select technology...</option>
                    {techs.map(t => <option key={t.id} value={t.id}>{t.icon} {t.name}</option>)}
                  </select>
                </div>
              </div>

              <div style={{ display: 'grid', gridTemplateColumns: 'repeat(3,1fr)', gap: '1rem', marginBottom: '1rem' }}>
                <div>
                  <label style={{ display: 'block', fontSize: '0.75rem', color: 'var(--text-muted)', marginBottom: '0.35rem', fontWeight: 600, textTransform: 'uppercase', letterSpacing: '0.04em' }}>Total Questions *</label>
                  <input type="number" min={1} max={50} value={totalQ} onChange={e => setTotalQ(+e.target.value)} required style={inpStyle} />
                </div>
                <div>
                  <label style={{ display: 'block', fontSize: '0.75rem', color: 'var(--text-muted)', marginBottom: '0.35rem', fontWeight: 600, textTransform: 'uppercase', letterSpacing: '0.04em' }}>Duration (min)</label>
                  <input type="number" min={5} value={duration} onChange={e => setDuration(+e.target.value)} style={inpStyle} />
                </div>
                <div>
                  <label style={{ display: 'block', fontSize: '0.75rem', color: 'var(--text-muted)', marginBottom: '0.35rem', fontWeight: 600, textTransform: 'uppercase', letterSpacing: '0.04em' }}>Passing Score (%)</label>
                  <input type="number" min={1} max={100} value={passing} onChange={e => setPassing(+e.target.value)} style={inpStyle} />
                </div>
              </div>

              {/* Difficulty Mix */}
              <div style={{ marginBottom: '1rem' }}>
                <label style={{ display: 'block', fontSize: '0.75rem', color: 'var(--text-muted)', marginBottom: '0.6rem', fontWeight: 600, textTransform: 'uppercase', letterSpacing: '0.04em' }}>
                  Difficulty Mix <span style={{ color: mixOk ? '#10b981' : '#ef4444', fontWeight: 700 }}>(must sum to {totalQ}; now {beg + inter + adv})</span>
                </label>
                <div style={{ display: 'grid', gridTemplateColumns: 'repeat(3,1fr)', gap: '0.75rem' }}>
                  {[{ label: '🟢 Beginner', val: beg, set: setBeg, c: '#10b981' },
                    { label: '🟡 Intermediate', val: inter, set: setInter, c: '#f59e0b' },
                    { label: '🔴 Advanced', val: adv, set: setAdv, c: '#ef4444' }].map(d => (
                    <div key={d.label}>
                      <label style={{ display: 'block', fontSize: '0.75rem', color: d.c, marginBottom: '0.25rem', fontWeight: 600 }}>{d.label}</label>
                      <input type="number" min={0} value={d.val} onChange={e => d.set(+e.target.value)} style={inpStyle} />
                    </div>
                  ))}
                </div>
              </div>

              <div style={{ marginBottom: '1.5rem' }}>
                <label style={{ display: 'block', fontSize: '0.75rem', color: 'var(--text-muted)', marginBottom: '0.35rem', fontWeight: 600, textTransform: 'uppercase', letterSpacing: '0.04em' }}>Candidate Instructions</label>
                <textarea value={instructions} onChange={e => setInstructions(e.target.value)} rows={2}
                  placeholder="e.g. Read each question carefully. No external resources allowed."
                  style={{ ...inpStyle, resize: 'vertical', lineHeight: 1.6 }} />
              </div>

              <button type="submit" className="btn-primary" disabled={creating || !mixOk}
                style={{ width: '100%', padding: '0.875rem', display: 'flex', alignItems: 'center', justifyContent: 'center', gap: '0.5rem', fontSize: '1rem' }}>
                {creating ? <><Spin />Creating...</> : <><CheckCircle size={17} />Create Assessment &amp; Proceed to Codes</>}
              </button>
            </form>
          </>
        )}

        {step === 2 && generatedAssessment && (
          <div className="animate-fade-in">
            {/* Assessment summary */}
            <div className="glass-panel" style={{ padding: '1.5rem', marginBottom: '1.5rem', borderTop: '3px solid #10b981' }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: '1rem' }}>
                <div style={{ fontSize: '2rem' }}>{generatedAssessment.technology_icon}</div>
                <div>
                  <h2 style={{ fontWeight: 700 }}>{generatedAssessment.title}</h2>
                  <div style={{ display: 'flex', gap: '0.5rem', flexWrap: 'wrap', marginTop: '0.35rem' }}>
                    <Badge color="#6366f1">{generatedAssessment.technology_name}</Badge>
                    <Badge color="#94a3b8">{generatedAssessment.total_questions} Questions</Badge>
                    <Badge color="#f59e0b">{generatedAssessment.duration_minutes} min</Badge>
                    <Badge color="#10b981">Pass {generatedAssessment.passing_score}%</Badge>
                  </div>
                </div>
              </div>
            </div>

            <div className="glass-panel" style={{ padding: '1.5rem', marginBottom: '1.5rem', textAlign: 'center' }}>
              <h3 style={{ fontWeight: 700, marginBottom: '0.5rem', fontSize: '1.1rem' }}>Assessment Access Code</h3>
              <p style={{ color: 'var(--text-muted)', fontSize: '0.85rem', marginBottom: '1.25rem' }}>
                Share this code with all candidates. They will enter their details when joining.
              </p>
              
              <div style={{ display: 'inline-flex', alignItems: 'center', gap: '1rem', background: 'rgba(16,185,129,0.06)', border: '1px solid rgba(16,185,129,0.2)', borderRadius: '10px', padding: '1rem 2rem' }}>
                <span style={{ fontFamily: 'var(--font-mono)', fontSize: '1.75rem', fontWeight: 800, color: '#6ee7b7', letterSpacing: '4px' }}>
                  {generatedAssessment.access_code}
                </span>
                <button className="btn-icon" onClick={() => copyCode(generatedAssessment.access_code || '')} title="Copy Code" style={{ background: 'rgba(255,255,255,0.1)', padding: '0.5rem' }}>
                  {copiedIdx ? <CheckCheck size={18} color="#10b981" /> : <Copy size={18} />}
                </button>
              </div>
              
              <div style={{ marginTop: '1.5rem', fontSize: '0.825rem', color: 'var(--text-muted)' }}>
                💡 Candidates can join at: <code style={{ color: 'var(--text-main)', padding: '2px 6px', background: 'rgba(255,255,255,0.05)', borderRadius: '4px' }}>{window.location.origin}/</code>
              </div>
            </div>

            <div style={{ display: 'flex', gap: '0.75rem', flexWrap: 'wrap', justifyContent: 'center' }}>
              <button className="btn-secondary" onClick={() => navigate(`/recruiter/assessment/${generatedAssessment.id}/results`)}>
                View Results Dashboard
              </button>
              <button className="btn-primary" onClick={() => { setStep(1); setCommand(''); setGeneratedAssessment(null); }} style={{ display: 'flex', alignItems: 'center', gap: '0.4rem' }}>
                <Plus size={15} /> Create Another
              </button>
            </div>
          </div>
        )}
      </div>
    </>
  );
}

// ─────────────────────────────────────────────────────────────────
// ALL ASSESSMENTS PAGE
// ─────────────────────────────────────────────────────────────────
function AllAssessments() {
  const navigate = useNavigate();
  const [assessments, setAssessments] = useState<Assessment[]>([]);
  const [loading, setLoading] = useState(true);

  const load = () => { setLoading(true); get('/admin/assessments').then(a => { setAssessments(a); setLoading(false); }).catch(() => setLoading(false)); };
  useEffect(load, []);

  return (
    <>
      <RecruiterNav active="/recruiter/assessments" />
      <div className="animate-fade-in" style={{ maxWidth: '1000px', margin: '0 auto', padding: '2rem 1.5rem' }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '1.75rem' }}>
          <div>
            <h1 style={{ fontSize: '1.5rem', fontWeight: 800, letterSpacing: '-0.03em' }}>All Assessments</h1>
            <p style={{ color: 'var(--text-muted)', fontSize: '0.825rem' }}>{assessments.length} assessments created</p>
          </div>
          <button className="btn-primary" onClick={() => navigate('/recruiter/create')} style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
            <Plus size={15} /> New
          </button>
        </div>

        <div className="glass-panel" style={{ overflow: 'hidden' }}>
          {loading ? <div style={{ padding: '3rem', textAlign: 'center' }}><Spin /></div>
            : assessments.length === 0 ? (
              <div style={{ padding: '3rem', textAlign: 'center', color: 'var(--text-muted)' }}>
                <ClipboardList size={40} style={{ opacity: 0.3, marginBottom: '0.75rem' }} />
                <p>No assessments yet.</p>
              </div>
            ) : assessments.map(a => (
              <div key={a.id} className="assessment-card" onClick={() => navigate(`/recruiter/assessment/${a.id}`)}>
                <div style={{ fontSize: '1.75rem' }}>{a.technology_icon}</div>
                <div style={{ flex: 1 }}>
                  <div style={{ fontWeight: 600, marginBottom: '0.3rem' }}>{a.title}</div>
                  <div style={{ display: 'flex', gap: '0.5rem', flexWrap: 'wrap' }}>
                    <Badge color="#6366f1">{a.technology_name}</Badge>
                    <Badge color="#94a3b8">{a.total_questions} Qs · {a.duration_minutes}min</Badge>
                    <Badge color="#f59e0b">Pass {a.passing_score}%</Badge>
                    {!a.is_active && <Badge color="#ef4444">Inactive</Badge>}
                  </div>
                </div>
                <div style={{ textAlign: 'right' }}>
                  <div style={{ fontWeight: 700, fontSize: '1.25rem' }}>{a.session_count}</div>
                  <div style={{ fontSize: '0.7rem', color: 'var(--text-muted)' }}>candidates</div>
                </div>
                <ArrowRight size={16} color="var(--text-muted)" />
              </div>
            ))}
        </div>
      </div>
    </>
  );
}

// ─────────────────────────────────────────────────────────────────
// SCHEDULE INTERVIEWS MODAL
// ─────────────────────────────────────────────────────────────────
function ScheduleInterviewsModal({
  isOpen, onClose, candidates, assessmentTitle
}: {
  isOpen: boolean; onClose: () => void; candidates: Session[]; assessmentTitle: string;
}) {
  const [interviewers, setInterviewers] = useState<any[]>([]);
  const [loading, setLoading] = useState(false);
  const [scheduling, setScheduling] = useState(false);

  const [date, setDate] = useState('');
  const [startTime, setStartTime] = useState('');
  const [duration, setDuration] = useState(45);
  const [breakTime, setBreakTime] = useState(15);
  const [selectedInterviewer, setSelectedInterviewer] = useState('');
  const [numCandidates, setNumCandidates] = useState(candidates.length);

  useEffect(() => {
    if (isOpen) {
      setLoading(true);
      fetch('http://127.0.0.1:8000/api/v1/interviewers/detailed')
        .then(r => r.json())
        .then(data => { setInterviewers(data); setLoading(false); })
        .catch(e => { alert('Failed to fetch interviewers'); setLoading(false); });
    }
  }, [isOpen]);

  if (!isOpen) return null;

  const handleSchedule = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!date || !startTime || !selectedInterviewer) return alert('Please fill required fields');
    if (numCandidates > candidates.length || numCandidates < 1) return alert('Invalid number of candidates');
    
    setScheduling(true);
    
    // Sort by highest score first, then slice
    const sorted = [...candidates].sort((a, b) => (b.percentage ?? 0) - (a.percentage ?? 0));
    const toSchedule = sorted.slice(0, numCandidates);

    try {
      // 1. Fetch P2 Candidates to map emails to candidate_ids
      const cRes = await fetch('http://127.0.0.1:8000/api/v1/candidates/detailed');
      const allP2Candidates = await cRes.json();
      const p2CandidateMap = new Map();
      allP2Candidates.forEach((c: any) => p2CandidateMap.set(c.email, c.candidate_id));

      let currentStartTime = new Date(`1970-01-01T${startTime}`);
      let scheduledCount = 0;
      let missingCount = 0;

      for (const cand of toSchedule) {
        if (!cand.candidate_email) continue;
        const c_id = p2CandidateMap.get(cand.candidate_email);
        
        if (!c_id) {
          missingCount++;
          continue; // Missing in Phase 2 DB (edge case)
        }

        const hh = String(currentStartTime.getHours()).padStart(2, '0');
        const mm = String(currentStartTime.getMinutes()).padStart(2, '0');
        
        const res = await fetch('http://127.0.0.1:8000/api/v1/interviews', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            candidate_id: c_id,
            interviewer_id: selectedInterviewer,
            recruiter_id: "U-REC-01",
            interview_type: "TECHNICAL",
            scheduled_date: date,
            scheduled_time: `${hh}:${mm}:00`,
            duration_minutes: duration,
            platform: "JITSI_MEET"
          })
        });

        if (!res.ok) {
          const err = await res.json();
          throw new Error(err.detail || 'Failed to schedule');
        }

        scheduledCount++;
        currentStartTime.setMinutes(currentStartTime.getMinutes() + duration + breakTime);
      }
      
      let msg = `✅ Successfully scheduled ${scheduledCount} interviews for ${assessmentTitle}!\n\n`;
      msg += `📧 Automated emails containing Jitsi Meet links have been dispatched to both the candidates and the interviewer's Gmail accounts.`;
      if (missingCount > 0) msg += `\n\n⚠️ Note: ${missingCount} candidate(s) could not be scheduled because they were missing in the Interview Management system.`;
      
      alert(msg);
      onClose();
    } catch(err: any) {
      alert("Scheduling error: " + err.message);
    } finally {
      setScheduling(false);
    }
  };

  return (
    <div style={{ position: 'fixed', top: 0, left: 0, right: 0, bottom: 0, background: 'rgba(0,0,0,0.7)', backdropFilter: 'blur(5px)', display: 'flex', alignItems: 'center', justifyContent: 'center', zIndex: 9999 }}>
      <div className="glass-panel" style={{ width: '100%', maxWidth: '480px', padding: '2rem' }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '1.5rem' }}>
          <h2 style={{ fontSize: '1.2rem', fontWeight: 800, margin: 0, display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
            <Calendar size={20} color="#10b981" /> Schedule Interviews
          </h2>
          <button className="btn-icon" onClick={onClose}><XCircle size={20} /></button>
        </div>
        
        <p style={{ fontSize: '0.85rem', color: 'var(--text-muted)', marginBottom: '1.5rem' }}>
          Schedule 1-on-1 video interviews for candidates who passed the <strong>{assessmentTitle}</strong> assessment.
        </p>
        
        <form onSubmit={handleSchedule}>
          <div className="form-group">
            <label className="form-label">Number of Candidates to Interview</label>
            <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', fontSize: '0.8rem', color: 'var(--text-muted)' }}>
              <input type="number" className="form-input" min={1} max={candidates.length} value={numCandidates} onChange={e => setNumCandidates(parseInt(e.target.value))} required style={{ width: '80px' }} />
              out of {candidates.length} shortlisted candidates (top scorers selected first)
            </div>
          </div>

          <div className="form-group">
            <label className="form-label">Select Interviewer</label>
            <select className="form-input" value={selectedInterviewer} onChange={e => setSelectedInterviewer(e.target.value)} required>
              <option value="">-- Choose an interviewer --</option>
              {loading ? <option disabled>Loading...</option> : interviewers.map(i => (
                <option key={i.interviewer_id} value={i.interviewer_id}>{i.name} ({i.expertise})</option>
              ))}
            </select>
          </div>

          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '1rem' }}>
            <div className="form-group">
              <label className="form-label">Interview Date</label>
              <input type="date" className="form-input" value={date} onChange={e => setDate(e.target.value)} required />
            </div>
            <div className="form-group">
              <label className="form-label">First Start Time</label>
              <input type="time" className="form-input" value={startTime} onChange={e => setStartTime(e.target.value)} required />
            </div>
          </div>

          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '1rem' }}>
            <div className="form-group">
              <label className="form-label">Duration (minutes)</label>
              <input type="number" className="form-input" value={duration} onChange={e => setDuration(parseInt(e.target.value))} min={15} max={180} step={15} required />
            </div>
            <div className="form-group">
              <label className="form-label">Break Between (minutes)</label>
              <input type="number" className="form-input" value={breakTime} onChange={e => setBreakTime(parseInt(e.target.value))} min={0} max={60} step={5} required />
            </div>
          </div>

          <button type="submit" className="btn-green" disabled={scheduling || candidates.length === 0} style={{ width: '100%', padding: '0.875rem', marginTop: '1rem', display: 'flex', alignItems: 'center', justifyContent: 'center', gap: '0.5rem', fontWeight: 600 }}>
            {scheduling ? <><Spin /> Creating links & sending emails...</> : <><Video size={16} /> Create {numCandidates} Interview(s)</>}
          </button>
        </form>
      </div>
    </div>
  );
}

// ─────────────────────────────────────────────────────────────────
// ASSESSMENT DETAIL – Recruiter's view: candidates + results
// ─────────────────────────────────────────────────────────────────
function AssessmentDetail() {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();
  const [assessment, setAssessment] = useState<Assessment | null>(null);
  const [sessions, setSessions] = useState<Session[]>([]);
  const [loading, setLoading] = useState(true);
  const [threshold, setThreshold] = useState<number>(60);
  const [copied, setCopied] = useState(false);
  const [deleting, setDeleting] = useState(false);
  const [savingThresh, setSavingThresh] = useState(false);
  const [showScheduleModal, setShowScheduleModal] = useState(false);

  const load = () => {
    setLoading(true);
    Promise.all([
      get(`/admin/assessments/${id}`),
      get(`/admin/assessments/${id}/sessions`),
    ]).then(([a, s]) => {
      setAssessment(a);
      setSessions(s);
      setThreshold(a.passing_score ?? 0);
      setLoading(false);
    }).catch(() => setLoading(false));
  };
  useEffect(load, [id]);

  const saveThreshold = async () => {
    if (!assessment) return;
    setSavingThresh(true);
    try {
      await put(`/admin/assessments/${assessment.id}`, { passing_score: threshold });
      // update local assessment object to reflect the change visually if needed, though not strictly required
      setAssessment({ ...assessment, passing_score: threshold });
    } catch (e: any) {
      alert('Failed to save threshold: ' + e.message);
    } finally {
      setSavingThresh(false);
    }
  };

  const copyCode = () => {
    if (!assessment?.access_code) return;
    navigator.clipboard.writeText(assessment.access_code);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  const handleDelete = async () => {
    if (!assessment) return;
    if (!confirm(`Delete "${assessment.title}"? This will permanently remove all candidate sessions and results.`)) return;
    setDeleting(true);
    try {
      await del(`/admin/assessments/${assessment.id}`);
      navigate('/recruiter/assessments');
    } catch (e: any) {
      alert('Delete failed: ' + e.message);
      setDeleting(false);
    }
  };

  if (loading) return (
    <>
      <RecruiterNav active="/recruiter/assessments" />
      <div style={{ display: 'flex', justifyContent: 'center', padding: '5rem' }}><Spin /></div>
    </>
  );
  if (!assessment) return (
    <>
      <RecruiterNav active="/recruiter/assessments" />
      <div style={{ padding: '3rem', textAlign: 'center', color: 'var(--text-muted)' }}>Assessment not found.</div>
    </>
  );

  // Separate sessions by completion state
  const evaluated = sessions.filter(s => s.status === 'evaluated' || s.status === 'submitted');
  const inProgress = sessions.filter(s => s.status !== 'evaluated' && s.status !== 'submitted');

  // Live shortlist by threshold
  const shortlisted = evaluated.filter(s => (s.percentage ?? 0) >= threshold);
  const notShortlisted = evaluated.filter(s => (s.percentage ?? 0) < threshold);

  const rowStyle = (isShortlisted: boolean): React.CSSProperties => ({
    display: 'grid',
    gridTemplateColumns: '1fr 1fr auto auto auto',
    alignItems: 'center',
    gap: '0.75rem',
    padding: '0.9rem 1.25rem',
    borderBottom: '1px solid var(--glass-border)',
    cursor: 'pointer',
    transition: 'background 0.15s',
  });

  const CandidateRow = ({ s }: { s: Session }) => {
    const pct = s.percentage ?? null;
    const isShort = pct !== null && pct >= threshold;
    const pctColor = pct === null ? 'var(--text-muted)' : isShort ? '#10b981' : '#ef4444';
    return (
      <div style={rowStyle(isShort)}
        onClick={() => navigate(`/recruiter/result/${s.id}`)}
        onMouseEnter={e => (e.currentTarget.style.background = 'rgba(255,255,255,0.03)')}
        onMouseLeave={e => (e.currentTarget.style.background = 'transparent')}>
        {/* Name + email */}
        <div>
          <div style={{ fontWeight: 600, fontSize: '0.92rem' }}>{s.candidate_name || '—'}</div>
          <div style={{ fontSize: '0.78rem', color: 'var(--text-muted)' }}>{s.candidate_email || '—'}</div>
        </div>
        {/* Status */}
        <div><StatusBadge status={s.status} /></div>
        {/* Score */}
        <div style={{ textAlign: 'right', minWidth: '70px' }}>
          {pct !== null ? (
            <>
              <div style={{ fontWeight: 800, fontSize: '1.1rem', color: pctColor }}>{pct.toFixed(1)}%</div>
              <div style={{ fontSize: '0.72rem', color: 'var(--text-muted)' }}>{s.score ?? 0} pts</div>
            </>
          ) : (
            <span style={{ fontSize: '0.8rem', color: 'var(--text-muted)' }}>Pending</span>
          )}
        </div>
        {/* Pass/Fail badge */}
        <div style={{ minWidth: '80px' }}>
          {pct !== null ? (
            <Badge color={isShort ? '#10b981' : '#ef4444'}>
              {isShort ? '✓ Shortlisted' : '✗ Rejected'}
            </Badge>
          ) : null}
        </div>
        <ArrowRight size={14} color="var(--text-muted)" />
      </div>
    );
  };

  return (
    <>
      <RecruiterNav active="/recruiter/assessments" />
      <div className="animate-fade-in" style={{ maxWidth: '1020px', margin: '0 auto', padding: '2rem 1.5rem' }}>

        {/* ── Header ── */}
        <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '1.75rem', gap: '1rem', flexWrap: 'wrap' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem' }}>
            <button className="btn-icon" onClick={() => navigate('/recruiter/assessments')}><ChevronLeft size={18} /></button>
            <div>
              <h1 style={{ fontSize: '1.5rem', fontWeight: 800, letterSpacing: '-0.03em' }}>{assessment.title}</h1>
              <p style={{ color: 'var(--text-muted)', fontSize: '0.825rem' }}>Candidate Results & Shortlisting</p>
            </div>
          </div>
          <button
            onClick={handleDelete}
            disabled={deleting}
            style={{
              display: 'flex', alignItems: 'center', gap: '0.4rem',
              background: 'rgba(239,68,68,0.12)', border: '1px solid rgba(239,68,68,0.3)',
              color: '#f87171', padding: '0.5rem 1rem', borderRadius: '8px',
              cursor: deleting ? 'not-allowed' : 'pointer', fontSize: '0.85rem', fontWeight: 600,
              transition: 'background 0.15s',
            }}
            onMouseEnter={e => !deleting && (e.currentTarget.style.background = 'rgba(239,68,68,0.22)')}
            onMouseLeave={e => (e.currentTarget.style.background = 'rgba(239,68,68,0.12)')}
          >
            <Trash2 size={15} /> {deleting ? 'Deleting…' : 'Delete Assessment'}
          </button>
        </div>

        {/* ── Assessment Info + Access Code ── */}
        <div className="glass-panel" style={{ padding: '1.25rem 1.5rem', marginBottom: '1.5rem', display: 'flex', flexWrap: 'wrap', gap: '1.5rem', alignItems: 'center', justifyContent: 'space-between' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '1rem' }}>
            <div style={{ fontSize: '2.25rem' }}>{assessment.technology_icon}</div>
            <div>
              <div style={{ display: 'flex', gap: '0.4rem', flexWrap: 'wrap', marginBottom: '0.25rem' }}>
                <Badge color="#6366f1">{assessment.technology_name}</Badge>
                <Badge color="#94a3b8">{assessment.total_questions} Questions</Badge>
                <Badge color="#f59e0b">{assessment.duration_minutes} min</Badge>
              </div>
              <div style={{ fontSize: '0.78rem', color: 'var(--text-muted)' }}>
                Created {new Date(assessment.created_at).toLocaleDateString()} · {sessions.length} candidates attempted
              </div>
            </div>
          </div>
          {/* Access Code */}
          <div style={{ background: 'rgba(16,185,129,0.07)', border: '1px solid rgba(16,185,129,0.2)', borderRadius: '10px', padding: '0.75rem 1.25rem', textAlign: 'center' }}>
            <div style={{ fontSize: '0.7rem', color: 'var(--text-muted)', fontWeight: 700, textTransform: 'uppercase', letterSpacing: '0.05em', marginBottom: '0.35rem' }}>
              🔑 Share Access Code
            </div>
            <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem' }}>
              <span style={{ fontFamily: 'var(--font-mono)', fontSize: '1.35rem', fontWeight: 900, color: '#6ee7b7', letterSpacing: '3px' }}>
                {assessment.access_code}
              </span>
              <button className="btn-icon" onClick={copyCode} title="Copy code">
                {copied ? <CheckCheck size={15} color="#10b981" /> : <Copy size={15} />}
              </button>
            </div>
            <div style={{ fontSize: '0.72rem', color: 'var(--text-muted)', marginTop: '0.25rem' }}>
              Share with all candidates
            </div>
          </div>
        </div>

        {/* ── Threshold Control ── */}
        <div className="glass-panel" style={{ padding: '1.25rem 1.5rem', marginBottom: '1.5rem', display: 'flex', alignItems: 'center', justifyContent: 'space-between', flexWrap: 'wrap', gap: '1rem' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem' }}>
            <Filter size={20} color="var(--primary)" />
            <div>
              <div style={{ fontWeight: 700, fontSize: '0.95rem' }}>Shortlisting Threshold</div>
              <div style={{ fontSize: '0.8rem', color: 'var(--text-muted)' }}>
                Candidates at or above this score are moved to the Shortlisted list.
              </div>
            </div>
          </div>
          <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem' }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', background: 'rgba(8,14,26,0.6)', border: '1px solid var(--glass-border)', padding: '0.4rem 0.75rem', borderRadius: '8px' }}>
              <input
                type="number" min="0" max="100" value={threshold}
                onChange={e => setThreshold(Number(e.target.value))}
                style={{
                  background: 'transparent', border: 'none', color: 'var(--text-main)',
                  fontSize: '1.2rem', width: '50px', textAlign: 'center', fontWeight: 800, outline: 'none',
                }}
              />
              <span style={{ fontSize: '1.2rem', fontWeight: 700, color: 'var(--text-muted)' }}>%</span>
            </div>
            <button
              className="btn-primary"
              onClick={saveThreshold}
              disabled={savingThresh}
              style={{ padding: '0.6rem 1rem', fontSize: '0.85rem' }}
            >
              {savingThresh ? 'Saving...' : 'Save Threshold'}
            </button>
          </div>
        </div>

        {/* ── Candidates Table ── */}
        {evaluated.length === 0 && inProgress.length === 0 ? (
          <div className="glass-panel" style={{ padding: '3rem', textAlign: 'center', color: 'var(--text-muted)' }}>
            <Users size={40} style={{ opacity: 0.25, marginBottom: '0.75rem' }} />
            <p style={{ fontWeight: 600 }}>No candidates yet</p>
            <p style={{ fontSize: '0.85rem', marginTop: '0.3rem' }}>
              Share the access code <strong style={{ color: '#6ee7b7' }}>{assessment.access_code}</strong> with your candidates.
            </p>
          </div>
        ) : (
          <>
            {/* Shortlisted candidates */}
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '1rem' }}>
              <h3 style={{ fontWeight: 800, fontSize: '1.1rem', color: '#10b981', display: 'flex', alignItems: 'center', gap: '0.5rem', margin: 0 }}>
                <CheckCircle size={18} /> Shortlisted Candidates ({shortlisted.length})
              </h3>
              {shortlisted.length > 0 && (
                <button 
                  className="btn-green"
                  style={{ padding: '0.5rem 1rem', fontSize: '0.8rem', display: 'flex', alignItems: 'center', gap: '0.4rem' }}
                  onClick={() => setShowScheduleModal(true)}
                >
                  <Calendar size={14} /> Schedule Interviews
                </button>
              )}
            </div>
            
            <ScheduleInterviewsModal 
              isOpen={showScheduleModal} 
              onClose={() => setShowScheduleModal(false)} 
              candidates={shortlisted} 
              assessmentTitle={assessment.title}
            />

            {shortlisted.length > 0 ? (
              <div className="glass-panel" style={{ overflow: 'hidden', marginBottom: '2rem' }}>
                <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr auto auto auto', gap: '0.75rem', padding: '0.6rem 1.25rem', background: 'rgba(16,185,129,0.05)', borderBottom: '1px solid var(--glass-border)', fontSize: '0.72rem', color: 'var(--text-muted)', fontWeight: 700, textTransform: 'uppercase', letterSpacing: '0.05em' }}>
                  <span>Candidate</span>
                  <span>Status</span>
                  <span style={{ textAlign: 'right' }}>Score</span>
                  <span>Result</span>
                  <span></span>
                </div>
                {shortlisted.map(s => <CandidateRow key={s.id} s={s} />)}
              </div>
            ) : (
              <div className="glass-panel" style={{ padding: '2rem', textAlign: 'center', color: 'var(--text-muted)', fontSize: '0.9rem', marginBottom: '2rem' }}>
                No candidates meet the {threshold}% threshold yet.
              </div>
            )}

            {/* Rejected candidates */}
            <h3 style={{ fontWeight: 800, fontSize: '1.1rem', color: '#ef4444', marginBottom: '1rem', display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
              <XCircle size={18} /> Rejected / Not Shortlisted ({notShortlisted.length})
            </h3>
            {notShortlisted.length > 0 ? (
              <div className="glass-panel" style={{ overflow: 'hidden', marginBottom: '2rem' }}>
                <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr auto auto auto', gap: '0.75rem', padding: '0.6rem 1.25rem', background: 'rgba(239,68,68,0.05)', borderBottom: '1px solid var(--glass-border)', fontSize: '0.72rem', color: 'var(--text-muted)', fontWeight: 700, textTransform: 'uppercase', letterSpacing: '0.05em' }}>
                  <span>Candidate</span>
                  <span>Status</span>
                  <span style={{ textAlign: 'right' }}>Score</span>
                  <span>Result</span>
                  <span></span>
                </div>
                {notShortlisted.map(s => <CandidateRow key={s.id} s={s} />)}
              </div>
            ) : (
              <div className="glass-panel" style={{ padding: '2rem', textAlign: 'center', color: 'var(--text-muted)', fontSize: '0.9rem', marginBottom: '2rem' }}>
                No candidates rejected.
              </div>
            )}

            {/* In-progress / pending candidates */}
            {inProgress.length > 0 && (
              <div>
                <h3 style={{ fontWeight: 700, fontSize: '0.9rem', color: 'var(--text-muted)', marginBottom: '0.75rem', display: 'flex', alignItems: 'center', gap: '0.4rem' }}>
                  <Clock size={15} /> In Progress / Not Submitted ({inProgress.length})
                </h3>
                <div className="glass-panel" style={{ overflow: 'hidden' }}>
                  {inProgress.map((s, i) => (
                    <div key={s.id} style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', padding: '0.8rem 1.25rem', borderBottom: i < inProgress.length - 1 ? '1px solid var(--glass-border)' : 'none' }}>
                      <div>
                        <div style={{ fontWeight: 600, fontSize: '0.9rem' }}>{s.candidate_name || 'Unknown'}</div>
                        <div style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>{s.candidate_email || '—'}</div>
                      </div>
                      <StatusBadge status={s.status} />
                    </div>
                  ))}
                </div>
              </div>
            )}
          </>
        )}
      </div>
    </>
  );
}


// ─────────────────────────────────────────────────────────────────
// SINGLE RESULT PAGE – detailed result per candidate
// ─────────────────────────────────────────────────────────────────
function SingleResult() {
  const { sessionId } = useParams<{ sessionId: string }>();
  const navigate = useNavigate();
  const [result, setResult] = useState<Result | null>(null);
  const [loading, setLoading] = useState(true);
  const [err, setErr] = useState('');

  useEffect(() => {
    get(`/admin/results/${sessionId}`).then(setResult).catch(e => setErr(e.message)).finally(() => setLoading(false));
  }, [sessionId]);

  if (loading) return <><RecruiterNav active="/recruiter/results" /><div style={{ padding: '5rem', textAlign: 'center' }}><Spin /></div></>;
  if (err || !result) return <><RecruiterNav active="/recruiter/results" /><div style={{ padding: '3rem', textAlign: 'center', color: 'var(--text-muted)' }}><Err msg={err || 'Result not found'} /></div></>;

  const scoreColor = result.passed ? '#10b981' : '#ef4444';

  return (
    <>
      <RecruiterNav active="/recruiter/results" />
      <div className="animate-fade-in" style={{ maxWidth: '860px', margin: '0 auto', padding: '2rem 1.5rem' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem', marginBottom: '1.75rem' }}>
          <button className="btn-icon" onClick={() => navigate(-1)}><ChevronLeft size={18} /></button>
          <div>
            <h1 style={{ fontSize: '1.4rem', fontWeight: 800 }}>Result: {result.candidate_name}</h1>
            <p style={{ color: 'var(--text-muted)', fontSize: '0.825rem' }}>{result.assessment_title} · {result.technology_name}</p>
          </div>
        </div>

        {/* Hero Score */}
        <div className="glass-panel" style={{ padding: '2rem', marginBottom: '1.5rem', display: 'flex', alignItems: 'center', gap: '2rem', flexWrap: 'wrap', borderTop: `4px solid ${scoreColor}` }}>
          <div style={{ textAlign: 'center' }}>
            <div style={{ fontSize: '3.5rem', fontWeight: 900, color: scoreColor, lineHeight: 1, fontVariantNumeric: 'tabular-nums' }}>{result.percentage.toFixed(1)}%</div>
            <div style={{ fontSize: '0.8rem', color: 'var(--text-muted)', marginTop: '0.35rem' }}>{result.total_score} / {result.max_possible_score} pts</div>
            <div style={{ marginTop: '0.65rem' }}>
              <Badge color={scoreColor}>{result.passed ? '✅ PASSED' : '❌ FAILED'}</Badge>
            </div>
          </div>
          <div style={{ flex: 1, minWidth: '200px' }}>
            <div style={{ marginBottom: '0.5rem', display: 'flex', justifyContent: 'space-between', fontSize: '0.8rem' }}>
              <span style={{ color: 'var(--text-muted)' }}>Score</span>
              <span style={{ fontWeight: 600, color: scoreColor }}>{result.percentage.toFixed(1)}%</span>
            </div>
            <div className="progress-bar">
              <div className="progress-fill" style={{ width: `${result.percentage}%`, background: `linear-gradient(90deg, ${scoreColor}aa, ${scoreColor})` }} />
            </div>
            <div style={{ marginTop: '1.25rem', display: 'flex', flexDirection: 'column', gap: '0.35rem' }}>
              <div style={{ display: 'flex', gap: '0.5rem', alignItems: 'center', fontSize: '0.8rem', color: 'var(--text-muted)' }}>
                <User size={13} /> <strong style={{ color: 'var(--text-main)' }}>{result.candidate_name}</strong>
              </div>
              <div style={{ display: 'flex', gap: '0.5rem', alignItems: 'center', fontSize: '0.8rem', color: 'var(--text-muted)' }}>
                <Mail size={13} /> {result.candidate_email}
              </div>
            </div>
          </div>
        </div>

        {/* Strengths & Weaknesses */}
        {(result.strengths?.length || result.weaknesses?.length) ? (
          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '1rem', marginBottom: '1.5rem' }}>
            {result.strengths && result.strengths.length > 0 && (
              <div className="glass-panel" style={{ padding: '1.25rem', borderTop: '3px solid #10b981' }}>
                <h3 style={{ fontSize: '0.8rem', fontWeight: 700, color: '#10b981', marginBottom: '0.75rem' }}>💪 Strengths</h3>
                {result.strengths.map((s, i) => <p key={i} style={{ fontSize: '0.825rem', color: 'var(--text-muted)', marginBottom: '0.3rem', lineHeight: 1.5 }}>• {s}</p>)}
              </div>
            )}
            {result.weaknesses && result.weaknesses.length > 0 && (
              <div className="glass-panel" style={{ padding: '1.25rem', borderTop: '3px solid #ef4444' }}>
                <h3 style={{ fontSize: '0.8rem', fontWeight: 700, color: '#ef4444', marginBottom: '0.75rem' }}>📚 Areas to Improve</h3>
                {result.weaknesses.map((w, i) => <p key={i} style={{ fontSize: '0.825rem', color: 'var(--text-muted)', marginBottom: '0.3rem', lineHeight: 1.5 }}>• {w}</p>)}
              </div>
            )}
          </div>
        ) : null}

        {/* AI Feedback */}
        {result.ai_feedback && (
          <div className="glass-panel" style={{ padding: '1.25rem', marginBottom: '1.5rem', borderLeft: '3px solid var(--primary)' }}>
            <h3 style={{ fontSize: '0.8rem', fontWeight: 700, color: 'var(--primary)', marginBottom: '0.65rem', display: 'flex', alignItems: 'center', gap: '0.4rem' }}>
              <Bot size={13} /> AI Evaluation Feedback
            </h3>
            <p style={{ fontSize: '0.875rem', color: 'var(--text-muted)', lineHeight: 1.7 }}>{result.ai_feedback}</p>
          </div>
        )}

        {/* Per-question breakdown */}
        {result.per_question_scores && result.per_question_scores.length > 0 && (
          <div className="glass-panel" style={{ overflow: 'hidden' }}>
            <div style={{ padding: '1rem 1.5rem', borderBottom: '1px solid var(--glass-border)', fontWeight: 700, fontSize: '0.9rem' }}>
              📋 Question-by-Question Breakdown
            </div>
            {result.per_question_scores.map((q, i) => (
              <div key={i} style={{ padding: '1rem 1.5rem', borderBottom: i < result.per_question_scores!.length - 1 ? '1px solid var(--glass-border)' : 'none' }}>
                <div style={{ display: 'flex', gap: '0.75rem', alignItems: 'flex-start' }}>
                  <div style={{ flexShrink: 0, marginTop: '2px' }}>{q.is_correct ? <CheckCircle size={16} color="#10b981" /> : <XCircle size={16} color="#ef4444" />}</div>
                  <div style={{ flex: 1 }}>
                    <p style={{ fontSize: '0.875rem', marginBottom: '0.35rem', lineHeight: 1.5, fontWeight: 500 }}>{q.question_text}</p>
                    <div style={{ display: 'flex', gap: '0.5rem', marginBottom: '0.35rem' }}>
                      <Badge color={typeColor(q.question_type)}>{q.question_type}</Badge>
                    </div>
                    {q.candidate_answer && (
                      <div style={{ fontSize: '0.78rem', color: 'var(--text-muted)', padding: '0.35rem 0.6rem', background: 'rgba(255,255,255,0.04)', borderRadius: '6px', marginBottom: '0.3rem' }}>
                        <strong>Answer:</strong> {q.candidate_answer}
                      </div>
                    )}
                    {q.ai_feedback && <p style={{ fontSize: '0.775rem', color: 'var(--text-muted)', fontStyle: 'italic' }}>{q.ai_feedback}</p>}
                  </div>
                  <div style={{ fontWeight: 800, fontSize: '0.95rem', color: q.is_correct ? '#10b981' : '#ef4444', flexShrink: 0 }}>
                    {q.score}/{q.max_score}
                  </div>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
    </>
  );
}

// ─────────────────────────────────────────────────────────────────
// QUESTION BANK PAGE
// ─────────────────────────────────────────────────────────────────
function QuestionBank() {
  const navigate = useNavigate();
  const [questions, setQuestions] = useState<any[]>([]);
  const [techs, setTechs] = useState<Tech[]>([]);
  const [loading, setLoading] = useState(true);
  const [total, setTotal] = useState(0); const [page, setPage] = useState(1); const [totalPages, setTotalPages] = useState(1);
  const [search, setSearch] = useState(''); const [filterTech, setFilterTech] = useState(''); const [filterDiff, setFilterDiff] = useState('');

  const load = useCallback(async () => {
    setLoading(true);
    const params = new URLSearchParams({ page: String(page), page_size: '20' });
    if (search) params.set('search', search);
    if (filterTech) params.set('technology_id', filterTech);
    if (filterDiff) params.set('difficulty', filterDiff);
    const d = await get(`/admin/questions?${params}`).catch(() => ({ items: [], total: 0, total_pages: 1 }));
    setQuestions(d.items || []); setTotal(d.total || 0); setTotalPages(d.total_pages || 1); setLoading(false);
  }, [page, search, filterTech, filterDiff]);

  useEffect(() => { get('/admin/questions/technologies/list').then(setTechs).catch(() => {}); }, []);
  useEffect(() => { load(); }, [load]);

  const inpStyle = { background: 'rgba(8,14,26,0.6)', border: '1px solid var(--glass-border)', color: 'var(--text-main)', padding: '0.55rem 0.875rem', borderRadius: '8px', fontSize: '0.85rem' } as React.CSSProperties;

  return (
    <>
      <RecruiterNav active="/recruiter/questions" />
      <div className="animate-fade-in" style={{ maxWidth: '1100px', margin: '0 auto', padding: '2rem 1.5rem' }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '1.5rem' }}>
          <div>
            <h1 style={{ fontSize: '1.5rem', fontWeight: 800, letterSpacing: '-0.03em' }}>Question Bank</h1>
            <p style={{ color: 'var(--text-muted)', fontSize: '0.825rem' }}>{total} questions available</p>
          </div>
          <button className="btn-primary" onClick={() => navigate('/recruiter/create')} style={{ display: 'flex', alignItems: 'center', gap: '0.4rem', fontSize: '0.85rem', padding: '0.6rem 1.1rem' }}>
            <Plus size={14} /> New Assessment
          </button>
        </div>

        <div className="glass-panel" style={{ padding: '0.875rem 1rem', marginBottom: '1rem', display: 'flex', gap: '0.75rem', flexWrap: 'wrap', alignItems: 'center' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', flex: 1, minWidth: '180px' }}>
            <Search size={14} color="var(--text-muted)" />
            <input value={search} onChange={e => { setSearch(e.target.value); setPage(1); }} placeholder="Search questions..." style={{ ...inpStyle, width: '100%', background: 'transparent', border: 'none', outline: 'none' }} />
          </div>
          <select value={filterTech} onChange={e => { setFilterTech(e.target.value); setPage(1); }} style={{ ...inpStyle, cursor: 'pointer' }}>
            <option value="">All Technologies</option>
            {techs.map(t => <option key={t.id} value={t.id}>{t.icon} {t.name}</option>)}
          </select>
          <select value={filterDiff} onChange={e => { setFilterDiff(e.target.value); setPage(1); }} style={{ ...inpStyle, cursor: 'pointer' }}>
            <option value="">All Difficulties</option>
            <option value="beginner">🟢 Beginner</option>
            <option value="intermediate">🟡 Intermediate</option>
            <option value="advanced">🔴 Advanced</option>
          </select>
          <button className="btn-icon" onClick={load}><RefreshCw size={14} /></button>
        </div>

        <div className="glass-panel" style={{ overflow: 'hidden' }}>
          {loading ? <div style={{ padding: '3rem', textAlign: 'center' }}><Spin /></div>
            : questions.length === 0 ? (
              <div style={{ padding: '3rem', textAlign: 'center', color: 'var(--text-muted)' }}>
                <BookOpen size={40} style={{ opacity: 0.3, marginBottom: '0.75rem' }} />
                <p>No questions found.</p>
              </div>
            ) : questions.map((q, i) => (
              <div key={q.id} style={{ padding: '0.9rem 1.25rem', borderBottom: i < questions.length - 1 ? '1px solid var(--glass-border)' : 'none', display: 'flex', gap: '0.875rem', alignItems: 'flex-start' }}>
                <div style={{ flex: 1 }}>
                  <p style={{ fontSize: '0.875rem', marginBottom: '0.4rem', lineHeight: 1.5 }}>{q.question_text.length > 150 ? q.question_text.slice(0, 150) + '…' : q.question_text}</p>
                  <div style={{ display: 'flex', gap: '0.4rem', flexWrap: 'wrap' }}>
                    {q.technology && <Badge color="#6366f1">{q.technology.icon} {q.technology.name}</Badge>}
                    <Badge color={diffColor(q.difficulty)}>{q.difficulty}</Badge>
                    <Badge color={typeColor(q.question_type)}>{q.question_type}</Badge>
                    <span style={{ fontSize: '0.72rem', color: 'var(--text-muted)', alignSelf: 'center' }}>{q.max_score} pts</span>
                  </div>
                </div>
              </div>
            ))}
        </div>

        {totalPages > 1 && (
          <div style={{ display: 'flex', justifyContent: 'center', gap: '0.5rem', marginTop: '1rem', alignItems: 'center' }}>
            <button onClick={() => setPage(p => Math.max(1, p - 1))} disabled={page === 1} className="btn-secondary" style={{ padding: '0.4rem 0.75rem' }}><ChevronLeft size={15} /></button>
            <span style={{ fontSize: '0.825rem', color: 'var(--text-muted)' }}>Page {page} of {totalPages}</span>
            <button onClick={() => setPage(p => Math.min(totalPages, p + 1))} disabled={page === totalPages} className="btn-secondary" style={{ padding: '0.4rem 0.75rem' }}><ChevronRight size={15} /></button>
          </div>
        )}
      </div>
    </>
  );
}

// ─────────────────────────────────────────────────────────────────
// CANDIDATE – Info Page (after entering code)
// ─────────────────────────────────────────────────────────────────
function CandidateInfo() {
  const { code } = useParams<{ code: string }>();
  const navigate = useNavigate();
  const [info, setInfo] = useState<SessionInfo | null>(null);
  const [loading, setLoading] = useState(true);
  const [err, setErr] = useState('');
  const [name, setName] = useState('');
  const [email, setEmail] = useState('');
  const [starting, setStarting] = useState(false);

  useEffect(() => {
    fetch(`${API}/candidate/config/${code}`)
      .then(r => r.json()).then(d => {
        if (d.detail) { setErr(d.detail); return; }
        setInfo(d);
      }).catch(() => setErr('Failed to load assessment.')).finally(() => setLoading(false));
  }, [code, navigate]);

  const handleStart = async (e: React.FormEvent) => {
    e.preventDefault();
    setStarting(true);
    try {
      const r = await fetch(`${API}/candidate/config/${code}/start`, {
        method: 'POST', headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ candidate_name: name, candidate_email: email }),
      });
      const d = await r.json();
      if (!r.ok) { throw new Error(d.detail || 'Failed'); }
      navigate(`/candidate/session/${d.session.id}/test`);
    } catch (e: any) { setErr(e.message); setStarting(false); }
  };

  if (loading) return <div style={{ display: 'flex', justifyContent: 'center', padding: '5rem' }}><Spin /></div>;
  if (err) return <div style={{ maxWidth: '520px', margin: '4rem auto', padding: '0 1rem' }}><Err msg={err} /></div>;
  if (!info) return null;

  return (
    <div className="animate-fade-in" style={{ maxWidth: '560px', margin: '3rem auto', padding: '0 1rem' }}>
      <div className="glass-panel" style={{ padding: '2.5rem' }}>
        <div style={{ textAlign: 'center', marginBottom: '2rem' }}>
          <div style={{ fontSize: '3rem', marginBottom: '0.5rem' }}>{info.technology_icon}</div>
          <h1 style={{ fontSize: '1.4rem', fontWeight: 800, marginBottom: '0.25rem' }}>{info.assessment_title}</h1>
          <p style={{ color: 'var(--text-muted)', fontSize: '0.875rem' }}>{info.technology} Technical Assessment</p>
        </div>

        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(3,1fr)', gap: '0.75rem', marginBottom: '1.75rem' }}>
          {[{ icon: <FileQuestion size={16} />, label: 'Questions', value: info.total_questions },
            { icon: <Clock size={16} />, label: 'Duration', value: `${info.duration_minutes} min` },
            { icon: <Star size={16} />, label: 'Pass Score', value: `${info.passing_score}%` }].map(s => (
            <div key={s.label} className="glass-panel" style={{ padding: '0.875rem', textAlign: 'center' }}>
              <div style={{ color: 'var(--primary)', marginBottom: '0.25rem', display: 'flex', justifyContent: 'center' }}>{s.icon}</div>
              <div style={{ fontWeight: 800, fontSize: '1.1rem' }}>{s.value}</div>
              <div style={{ fontSize: '0.7rem', color: 'var(--text-muted)', marginTop: '1px' }}>{s.label}</div>
            </div>
          ))}
        </div>

        {info.instructions && (
          <div style={{ background: 'rgba(99,102,241,0.08)', border: '1px solid rgba(99,102,241,0.2)', borderRadius: '10px', padding: '0.875rem', marginBottom: '1.5rem', fontSize: '0.85rem', color: 'var(--text-muted)', lineHeight: 1.6 }}>
            📋 {info.instructions}
          </div>
        )}

        <form onSubmit={handleStart}>
          {err && <Err msg={err} />}
          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '0.75rem', marginBottom: '1.25rem' }}>
            <div>
              <label className="form-label" style={{ display: 'block', marginBottom: '0.35rem' }}>Your Name *</label>
              <input type="text" className="form-input" value={name} onChange={e => setName(e.target.value)} placeholder="Full name" required />
            </div>
            <div>
              <label className="form-label" style={{ display: 'block', marginBottom: '0.35rem' }}>Email *</label>
              <input type="email" className="form-input" value={email} onChange={e => setEmail(e.target.value)} placeholder="your@email.com" required />
            </div>
          </div>
          <button type="submit" className="btn-green" disabled={starting}
            style={{ width: '100%', padding: '0.9rem', display: 'flex', alignItems: 'center', justifyContent: 'center', gap: '0.5rem', fontSize: '1rem' }}>
            {starting ? <><Spin />Starting...</> : <>🚀 Begin Assessment <ArrowRight size={16} /></>}
          </button>
          <p style={{ textAlign: 'center', marginTop: '0.75rem', fontSize: '0.75rem', color: 'var(--text-muted)' }}>
            Timer starts immediately. You have {info.duration_minutes} minutes.
          </p>
        </form>
      </div>
    </div>
  );
}

// ─────────────────────────────────────────────────────────────────
// CANDIDATE – Test Page
// ─────────────────────────────────────────────────────────────────
function CandidateTest() {
  const { sessionId } = useParams<{ sessionId: string }>();
  const navigate = useNavigate();
  const [questions, setQuestions] = useState<CandidateQ[]>([]);
  const [answers, setAnswers] = useState<Record<string, { text?: string; option?: number }>>({});
  const [currentIdx, setCurrentIdx] = useState(0);
  const [timeLeft, setTimeLeft] = useState(0);
  const [submitting, setSubmitting] = useState(false);
  const [loading, setLoading] = useState(true);
  const [err, setErr] = useState('');
  const submittedRef = useRef(false);

  useEffect(() => {
    fetch(`${API}/candidate/session/${sessionId}`)
      .then(async r => {
        const info = await r.json();
        if (!r.ok) { setErr(info.detail || 'Invalid session.'); setLoading(false); return; }
        if (info.status === 'submitted' || info.status === 'evaluated') { navigate(`/candidate/session/${sessionId}/result`); return; }
        setQuestions(info.questions || []); 
        setTimeLeft((info.session?.duration_minutes || 60) * 60);
      }).catch(() => setErr('Connection failed.')).finally(() => setLoading(false));
  }, [sessionId, navigate]);

  // Timer
  useEffect(() => {
    if (timeLeft <= 0 || loading) return;
    const t = setInterval(() => {
      setTimeLeft(s => {
        if (s <= 1) { handleSubmit(); return 0; }
        return s - 1;
      });
    }, 1000);
    return () => clearInterval(t);
  }, [timeLeft, loading]);

  const saveAnswer = async (qid: string, text?: string, option?: number) => {
    try {
      await fetch(`${API}/candidate/session/${sessionId}/answer`, {
        method: 'POST', headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ question_id: qid, answer_text: text ?? null, selected_option: option ?? null }),
      });
    } catch {}
  };

  const handleSelect = (qid: string, idx: number) => {
    setAnswers(p => ({ ...p, [qid]: { option: idx } }));
    saveAnswer(qid, undefined, idx);
  };
  const handleText = (qid: string, text: string) => setAnswers(p => ({ ...p, [qid]: { text } }));
  const handleBlur = (qid: string) => saveAnswer(qid, answers[qid]?.text);

  const handleSubmit = async () => {
    if (submittedRef.current || submitting) return;
    submittedRef.current = true; setSubmitting(true);
    try {
      const r = await fetch(`${API}/candidate/session/${sessionId}/submit`, { method: 'POST' });
      if (r.ok) navigate(`/candidate/session/${sessionId}/result`);
      else { const d = await r.json(); setErr(d.detail || 'Submit failed.'); submittedRef.current = false; setSubmitting(false); }
    } catch { setErr('Submit failed.'); submittedRef.current = false; setSubmitting(false); }
  };

  const fmt = (s: number) => `${Math.floor(s / 60).toString().padStart(2, '0')}:${(s % 60).toString().padStart(2, '0')}`;
  const urgent = timeLeft > 0 && timeLeft < 300;

  if (loading) return <div style={{ display: 'flex', justifyContent: 'center', padding: '5rem' }}><Spin /></div>;
  if (err) return <div style={{ maxWidth: '520px', margin: '3rem auto', padding: '0 1rem' }}><Err msg={err} /></div>;
  if (questions.length === 0) return <div style={{ padding: '3rem', textAlign: 'center', color: 'var(--text-muted)' }}>No questions loaded.</div>;

  const cur = questions[currentIdx];
  const answered = Object.keys(answers).length;

  return (
    <div className="animate-fade-in" style={{ maxWidth: '820px', margin: '0 auto', padding: '1.5rem 1rem' }}>
      {/* Header bar */}
      <div className="glass-panel" style={{ padding: '0.875rem 1.25rem', marginBottom: '1.25rem', display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '1rem' }}>
          <span style={{ fontSize: '0.85rem', color: 'var(--text-muted)' }}>Q {currentIdx + 1} / {questions.length}</span>
          <div style={{ width: '140px', height: '5px', background: 'var(--glass-border)', borderRadius: '999px', overflow: 'hidden' }}>
            <div style={{ width: `${((currentIdx + 1) / questions.length) * 100}%`, height: '100%', background: 'var(--primary)', borderRadius: '999px', transition: 'width 0.3s' }} />
          </div>
          <span style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>{answered} answered</span>
        </div>
        <div style={{ display: 'flex', alignItems: 'center', gap: '0.45rem', fontWeight: 700, fontSize: '1.05rem', color: urgent ? '#ef4444' : 'var(--text-main)', animation: urgent ? 'pulse 1s infinite' : 'none' }}>
          <Clock size={15} style={{ color: urgent ? '#ef4444' : 'var(--text-muted)' }} />
          {fmt(timeLeft)}
        </div>
      </div>

      {/* Question card */}
      <div className="glass-panel" style={{ padding: '2rem', marginBottom: '1rem' }}>
        <div style={{ display: 'flex', gap: '0.5rem', marginBottom: '1.25rem', flexWrap: 'wrap' }}>
          <Badge color={diffColor(cur.difficulty)}>{cur.difficulty}</Badge>
          <Badge color={typeColor(cur.question_type)}>{cur.question_type}</Badge>
          <span style={{ fontSize: '0.72rem', color: 'var(--text-muted)', alignSelf: 'center' }}>{cur.max_score} pts</span>
        </div>
        <p style={{ fontSize: '1.05rem', lineHeight: 1.75, fontWeight: 500, marginBottom: '1.5rem' }}>{cur.question_text}</p>

        {(cur.question_type === 'mcq' || cur.question_type === 'true_false') && cur.options && (
          <div style={{ display: 'flex', flexDirection: 'column', gap: '0.65rem' }}>
            {cur.options.map((opt, idx) => (
              <button key={idx} className={`q-option ${answers[cur.id]?.option === idx ? 'selected' : ''}`}
                onClick={() => handleSelect(cur.id, idx)}>
                <span className="q-label">{opt.label}</span>
                {opt.text}
              </button>
            ))}
          </div>
        )}

        {(cur.question_type === 'short_answer' || cur.question_type === 'code') && (
          <textarea value={answers[cur.id]?.text || ''} onChange={e => handleText(cur.id, e.target.value)} onBlur={() => handleBlur(cur.id)}
            placeholder={cur.question_type === 'code' ? 'Write your code here...' : 'Type your answer here...'}
            rows={cur.question_type === 'code' ? 10 : 5}
            style={{ width: '100%', background: 'rgba(8,14,26,0.6)', border: '1px solid var(--glass-border)', color: 'var(--text-main)', padding: '0.875rem', borderRadius: '10px', fontSize: '0.9rem', fontFamily: cur.question_type === 'code' ? 'var(--font-mono)' : 'inherit', resize: 'vertical', lineHeight: 1.7, outline: 'none' }} />
        )}
      </div>

      {/* Navigation */}
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
        <button onClick={() => setCurrentIdx(i => Math.max(0, i - 1))} disabled={currentIdx === 0}
          className="btn-secondary" style={{ display: 'flex', alignItems: 'center', gap: '0.4rem' }}>
          <ChevronLeft size={15} /> Prev
        </button>

        {/* Dot nav */}
        <div style={{ display: 'flex', gap: '0.3rem', flexWrap: 'wrap', justifyContent: 'center', maxWidth: '360px' }}>
          {questions.map((q, i) => (
            <button key={i} onClick={() => setCurrentIdx(i)}
              style={{ width: '26px', height: '26px', borderRadius: '6px', border: 'none', cursor: 'pointer', fontSize: '0.7rem', fontWeight: 700, color: 'white', transition: 'all 0.15s', background: i === currentIdx ? 'var(--primary)' : answers[q.id] ? 'rgba(16,185,129,0.5)' : 'var(--glass-border)' }}>
              {i + 1}
            </button>
          ))}
        </div>

        {currentIdx < questions.length - 1 ? (
          <button onClick={() => setCurrentIdx(i => i + 1)} className="btn-secondary"
            style={{ display: 'flex', alignItems: 'center', gap: '0.4rem' }}>
            Next <ChevronRight size={15} />
          </button>
        ) : (
          <button onClick={handleSubmit} disabled={submitting} className="btn-green"
            style={{ display: 'flex', alignItems: 'center', gap: '0.4rem' }}>
            {submitting ? <><Spin />Submitting...</> : <><Send size={14} />Submit</>}
          </button>
        )}
      </div>

      {currentIdx < questions.length - 1 && (
        <div style={{ textAlign: 'center', marginTop: '1.25rem' }}>
          <button onClick={handleSubmit} disabled={submitting}
            style={{ background: 'transparent', border: '1px solid var(--glass-border)', color: 'var(--text-muted)', padding: '0.5rem 1.5rem', borderRadius: '8px', cursor: 'pointer', fontSize: '0.825rem' }}>
            {submitting ? 'Submitting...' : 'Submit Early'}
          </button>
        </div>
      )}
    </div>
  );
}

// ─────────────────────────────────────────────────────────────────
// CANDIDATE – Result Page
// ─────────────────────────────────────────────────────────────────
function CandidateResult() {
  const { sessionId } = useParams<{ sessionId: string }>();
  const navigate = useNavigate();
  const [result, setResult] = useState<Result | null>(null);
  const [loading, setLoading] = useState(true);
  const [err, setErr] = useState('');

  useEffect(() => {
    let attempts = 0;
    const tryFetch = () => {
      fetch(`${API}/candidate/session/${sessionId}/result`).then(async r => {
        const d = await r.json();
        if (r.ok) { setResult(d); setLoading(false); }
        else if (r.status === 404 && attempts < 6) { attempts++; setTimeout(tryFetch, 2500); }
        else { setErr(d.detail || 'Result not available.'); setLoading(false); }
      }).catch(() => { setErr('Failed.'); setLoading(false); });
    };
    tryFetch();
  }, [sessionId]);

  if (loading) return (
    <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center', minHeight: '60vh', gap: '1rem' }}>
      <Spin /><p style={{ color: 'var(--text-muted)' }}>Calculating your results… this may take a moment.</p>
    </div>
  );
  if (err || !result) return <div style={{ maxWidth: '520px', margin: '4rem auto', padding: '0 1rem' }}><Err msg={err || 'No result.'} /></div>;

  const sc = result.passed ? '#10b981' : '#ef4444';

  return (
    <div className="animate-fade-in" style={{ maxWidth: '680px', margin: '2rem auto', padding: '0 1rem' }}>
      {/* Hero */}
      <div className="glass-panel" style={{ padding: '2.5rem', textAlign: 'center', marginBottom: '1.5rem', borderTop: `4px solid ${sc}`, background: result.passed ? 'rgba(16,185,129,0.04)' : 'rgba(239,68,68,0.04)' }}>
        <div style={{ fontSize: '3.5rem', marginBottom: '0.5rem' }}>{result.passed ? '🎉' : '😔'}</div>
        <div className="animate-count" style={{ fontSize: '3.5rem', fontWeight: 900, color: sc, lineHeight: 1 }}>{result.percentage.toFixed(1)}%</div>
        <p style={{ color: 'var(--text-muted)', marginTop: '0.35rem' }}>{result.total_score} / {result.max_possible_score} points</p>
        <div style={{ margin: '1rem 0' }}>
          <Badge color={sc}>{result.passed ? '✅ ASSESSMENT PASSED' : '❌ ASSESSMENT FAILED'}</Badge>
        </div>
        {result.candidate_name && <p style={{ color: 'var(--text-muted)', fontSize: '0.85rem' }}>{result.candidate_name} · {result.assessment_title}</p>}
      </div>

      {(result.strengths?.length || result.weaknesses?.length) ? (
        <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '1rem', marginBottom: '1.5rem' }}>
          {result.strengths?.length ? (
            <div className="glass-panel" style={{ padding: '1.25rem', borderTop: '3px solid #10b981' }}>
              <h3 style={{ fontSize: '0.8rem', fontWeight: 700, color: '#10b981', marginBottom: '0.65rem' }}>💪 Strengths</h3>
              {result.strengths.map((s, i) => <p key={i} style={{ fontSize: '0.825rem', color: 'var(--text-muted)', marginBottom: '0.3rem', lineHeight: 1.5 }}>• {s}</p>)}
            </div>
          ) : null}
          {result.weaknesses?.length ? (
            <div className="glass-panel" style={{ padding: '1.25rem', borderTop: '3px solid #ef4444' }}>
              <h3 style={{ fontSize: '0.8rem', fontWeight: 700, color: '#ef4444', marginBottom: '0.65rem' }}>📚 Areas to Improve</h3>
              {result.weaknesses.map((w, i) => <p key={i} style={{ fontSize: '0.825rem', color: 'var(--text-muted)', marginBottom: '0.3rem', lineHeight: 1.5 }}>• {w}</p>)}
            </div>
          ) : null}
        </div>
      ) : null}

      {result.ai_feedback && (
        <div className="glass-panel" style={{ padding: '1.25rem', marginBottom: '1.5rem', borderLeft: '3px solid var(--primary)' }}>
          <h3 style={{ fontSize: '0.8rem', fontWeight: 700, color: 'var(--primary)', marginBottom: '0.65rem', display: 'flex', alignItems: 'center', gap: '0.4rem' }}>
            <Bot size={13} /> AI Feedback
          </h3>
          <p style={{ fontSize: '0.875rem', color: 'var(--text-muted)', lineHeight: 1.7 }}>{result.ai_feedback}</p>
        </div>
      )}

      {result.per_question_scores?.length ? (
        <div className="glass-panel" style={{ overflow: 'hidden', marginBottom: '1.5rem' }}>
          <div style={{ padding: '1rem 1.5rem', borderBottom: '1px solid var(--glass-border)', fontWeight: 700, fontSize: '0.875rem' }}>📋 Question Breakdown</div>
          {result.per_question_scores.map((q, i) => (
            <div key={i} style={{ padding: '0.875rem 1.5rem', borderBottom: i < result.per_question_scores!.length - 1 ? '1px solid var(--glass-border)' : 'none', display: 'flex', gap: '0.75rem', alignItems: 'flex-start' }}>
              <div style={{ marginTop: '2px', flexShrink: 0 }}>{q.is_correct ? <CheckCircle size={15} color="#10b981" /> : <XCircle size={15} color="#ef4444" />}</div>
              <div style={{ flex: 1 }}>
                <p style={{ fontSize: '0.85rem', lineHeight: 1.5, marginBottom: '0.25rem' }}>{q.question_text}</p>
                {q.ai_feedback && <p style={{ fontSize: '0.75rem', color: 'var(--text-muted)', fontStyle: 'italic' }}>{q.ai_feedback}</p>}
              </div>
              <span style={{ fontWeight: 800, color: q.is_correct ? '#10b981' : '#ef4444', flexShrink: 0 }}>{q.score}/{q.max_score}</span>
            </div>
          ))}
        </div>
      ) : null}

      <div style={{ textAlign: 'center' }}>
        <button className="btn-secondary" onClick={() => navigate('/')} style={{ padding: '0.75rem 2rem' }}>
          ← Back to Home
        </button>
      </div>
    </div>
  );
}

// ─────────────────────────────────────────────────────────────────
// AUTH GUARD
// ─────────────────────────────────────────────────────────────────
function RequireAuth({ children }: { children: JSX.Element }) {
  return localStorage.getItem('token') ? children : <Navigate to="/" replace />;
}

// ─────────────────────────────────────────────────────────────────
// MINIMAL NAVBAR for candidate pages
// ─────────────────────────────────────────────────────────────────
function CandidateNav() {
  const navigate = useNavigate();
  return (
    <nav className="navbar">
      <div className="brand" onClick={() => navigate('/')} style={{ cursor: 'pointer' }}>
        <Bot className="brand-icon" size={22} />
        <span>AI Assessor</span>
      </div>
      <button className="btn-secondary" onClick={() => navigate('/')} style={{ fontSize: '0.8rem', padding: '0.4rem 0.875rem' }}>
        ← Home
      </button>
    </nav>
  );
}

// ─────────────────────────────────────────────────────────────────
// PHASE 2 EMBEDS
// ─────────────────────────────────────────────────────────────────
function Phase2RecruiterDashboard() {
  return (
    <div style={{ display: 'flex', flexDirection: 'column', height: '100vh', background: 'var(--bg-main)' }}>
      <RecruiterNav active="/recruiter/interviews" />
      <div style={{ flex: 1, padding: '1.5rem', overflow: 'hidden' }}>
        <div className="glass-panel" style={{ width: '100%', height: '100%', padding: 0, overflow: 'hidden', borderRadius: '12px' }}>
          <iframe 
            src="http://127.0.0.1:8000/app/index.html?auto_email=recruiter@hiringco.com&auto_role=RECRUITER" 
            style={{ width: '100%', height: '100%', border: 'none', background: 'transparent' }}
            title="Phase 2 Recruiter Dashboard"
          />
        </div>
      </div>
    </div>
  );
}

function Phase2InterviewerDashboard() {
  const navigate = useNavigate();
  // Retrieve the interviewer data we saved in sessionStorage during login
  const p2user = JSON.parse(sessionStorage.getItem('p2user') || '{}');
  const email = p2user.email || 'interviewer@hiringco.com';

  return (
    <div style={{ display: 'flex', flexDirection: 'column', height: '100vh', background: 'var(--bg-main)' }}>
      <nav className="navbar">
        <div className="brand" onClick={() => navigate('/')} style={{ cursor: 'pointer' }}>
          <Bot className="brand-icon" size={22} />
          <span>AI Assessor</span>
        </div>
        <div style={{ display: 'flex', gap: '1rem', alignItems: 'center' }}>
          <span style={{ fontSize: '0.85rem', color: '#a5b4fc', fontWeight: 500 }}><Briefcase size={14} style={{ display: 'inline', verticalAlign: 'text-bottom', marginRight: '4px' }}/> Interviewer Portal</span>
          <button className="btn-secondary" onClick={() => { sessionStorage.clear(); navigate('/'); }} style={{ fontSize: '0.8rem', padding: '0.4rem 0.875rem' }}>
            <LogOut size={13} style={{ display: 'inline', marginRight: '4px' }} /> Logout
          </button>
        </div>
      </nav>
      <div style={{ flex: 1, padding: '1.5rem', overflow: 'hidden' }}>
        <div className="glass-panel" style={{ width: '100%', height: '100%', padding: 0, overflow: 'hidden', borderRadius: '12px' }}>
          <iframe 
            src={`http://127.0.0.1:8000/app/interviewer_profile.html?auto_email=${encodeURIComponent(email)}&auto_role=INTERVIEWER`}
            style={{ width: '100%', height: '100%', border: 'none', background: 'transparent' }}
            title="Phase 2 Interviewer Dashboard"
          />
        </div>
      </div>
    </div>
  );
}

// ─────────────────────────────────────────────────────────────────
// APP ROOT
// ─────────────────────────────────────────────────────────────────
export default function App() {
  return (
    <BrowserRouter>
      <div className="app-container">
        <Routes>
          {/* Landing */}
          <Route path="/" element={<><nav className="navbar"><div className="brand" style={{ cursor:'pointer' }} onClick={() => window.scrollTo(0,0)}><Bot className="brand-icon" size={22}/><span>AI Assessor</span></div></nav><LandingPage /></>} />

          {/* Recruiter routes */}
          <Route path="/recruiter/dashboard" element={<RequireAuth><RecruiterDashboard /></RequireAuth>} />
          <Route path="/recruiter/create" element={<RequireAuth><CreateAssessment /></RequireAuth>} />
          <Route path="/recruiter/assessments" element={<RequireAuth><AllAssessments /></RequireAuth>} />
          <Route path="/recruiter/assessment/:id" element={<RequireAuth><AssessmentDetail /></RequireAuth>} />
          <Route path="/recruiter/result/:sessionId" element={<RequireAuth><SingleResult /></RequireAuth>} />
          <Route path="/recruiter/questions" element={<RequireAuth><QuestionBank /></RequireAuth>} />
          <Route path="/recruiter/interviews" element={<RequireAuth><Phase2RecruiterDashboard /></RequireAuth>} />

          {/* Interviewer route */}
          <Route path="/interviewer/dashboard" element={<Phase2InterviewerDashboard />} />

          {/* Candidate routes */}
          <Route path="/candidate/:code" element={<><CandidateNav /><CandidateInfo /></>} />
          <Route path="/candidate/session/:sessionId/test" element={<><CandidateNav /><CandidateTest /></>} />
          <Route path="/candidate/session/:sessionId/result" element={<><CandidateNav /><CandidateResult /></>} />

          <Route path="*" element={<Navigate to="/" replace />} />
        </Routes>
        <footer style={{ padding: '1rem 2rem', textAlign: 'center', fontSize: '0.72rem', color: 'var(--text-muted)', borderTop: '1px solid var(--glass-border)' }}>
          AI Assessor · Technical Assessment Platform
        </footer>
      </div>
    </BrowserRouter>
  );
}
