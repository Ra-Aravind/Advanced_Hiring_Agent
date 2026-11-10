const $ = (selector) => document.querySelector(selector);
const $$ = (selector) => [...document.querySelectorAll(selector)];

let state = {
  currentUser: null,
  candidates: [],
  interviewers: [],
  interviews: []
};

// ── Utilities ─────────────────────────────────────────────────────────────────

function formatDate(date, time) {
  if (!date || !time) return "TBD";
  const d = new Date(`${date}T${time}`);
  return d.toLocaleString([], { day: "2-digit", month: "short", year: "numeric", hour: "2-digit", minute: "2-digit" });
}

function statusClass(status) {
  const s = (status || "").toUpperCase();
  if (s === "COMPLETED") return "completed";
  if (s === "CANCELLED" || s === "NO_SHOW" || s === "PENDING_FEEDBACK") return "pending";
  return "scheduled";
}

function showToast(message, type = "success") {
  const toast = document.createElement("div");
  toast.className = `toast toast-${type}`;
  toast.textContent = message;
  document.body.appendChild(toast);
  setTimeout(() => toast.classList.add("show"), 10);
  setTimeout(() => {
    toast.classList.remove("show");
    setTimeout(() => toast.remove(), 300);
  }, 3500);
}

// ── Rendering ─────────────────────────────────────────────────────────────────

function renderDashboard() {
  const upcoming = state.interviews.filter(i => i.status === "SCHEDULED").length;
  const todayStr = new Date().toISOString().split("T")[0];
  const today = state.interviews.filter(i => i.scheduled_date === todayStr).length;
  const completed = state.interviews.filter(i => i.status === "COMPLETED").length;
  const eligible = state.candidates.filter(c => c.interview_eligible).length;

  $("#statsGrid").innerHTML = [
    ["Upcoming Interviews", upcoming],
    ["Today's Interviews", today],
    ["Completed", completed],
    ["Eligible Candidates", eligible]
  ].map(([label, value]) =>
    `<div class="stat-card"><div class="stat-label">${label}</div><div class="stat-value">${value}</div></div>`
  ).join("");

  const upcoming_list = state.interviews.filter(i => i.status === "SCHEDULED" || i.status === "IN_PROGRESS");

  $("#upcomingList").innerHTML = upcoming_list.length
    ? upcoming_list.map(i => `
        <div class="interview-row">
          <div><div class="person">${i.candidate_name}</div><div class="subtle">${i.candidate_skill || "General"} · ${i.duration_minutes} min</div></div>
          <div><div class="person">${i.interviewer_name}</div><div class="subtle">Interviewer</div></div>
          <div><div class="person">${formatDate(i.scheduled_date, i.scheduled_time)}</div><div class="subtle">${i.platform}</div></div>
          <span class="badge ${statusClass(i.status)}">${i.status}</span>
        </div>`).join("")
    : `<p class="subtle" style="padding:10px 0">No upcoming interviews.</p>`;
}

function renderCandidates() {
  $("#candidateTable").innerHTML = state.candidates.length
    ? state.candidates.map(c => `
        <tr>
          <td><strong>${c.name}</strong><div class="subtle">${c.email}</div></td>
          <td>${c.primary_skill || "-"}</td>
          <td>${c.phase1_score != null ? c.phase1_score + "%" : "-"}</td>
          <td><span class="badge ${c.interview_eligible ? "completed" : "pending"}">${c.interview_eligible ? "Eligible" : "Not Eligible"}</span></td>
        </tr>`).join("")
    : `<tr><td colspan="4" style="text-align:center;color:var(--muted);padding:20px">No candidates found.</td></tr>`;
}

function renderInterviewers() {
  $("#interviewerCards").innerHTML = state.interviewers.length
    ? state.interviewers.map(i => `
        <div class="interviewer-card">
          <div style="display:flex;justify-content:space-between;align-items:flex-start">
            <div class="avatar">${i.name.slice(0,1).toUpperCase()}</div>
            <button class="icon-btn" style="color:#dc2626;font-size:18px" title="Remove Interviewer" onclick="removeInterviewer('${i.interviewer_id}', '${i.name.replace(/'/g,"\\'")}')">×</button>
          </div>
          <strong>${i.name}</strong>
          <div class="subtle">${i.expertise || i.department || "N/A"}</div>
          <div class="subtle" style="margin-top:4px">${i.email}</div>
          <div style="margin-top:12px;display:flex;gap:8px;align-items:center;flex-wrap:wrap;">
            <span class="badge ${i.availability_status === "AVAILABLE" ? "completed" : "pending"}">${i.availability_status === "AVAILABLE" ? "Available" : "Busy"}</span>
            <button class="text-btn" style="font-size:11px" onclick="toggleAvailability('${i.interviewer_id}','${i.availability_status}')">
              ${i.availability_status === "AVAILABLE" ? "Set Busy" : "Set Available"}
            </button>
          </div>
          <div style="margin-top: 12px;">
            <a href="interviewer_profile.html" target="_blank" class="secondary-btn" style="font-size:12px;padding:6px 12px;text-decoration:none;display:inline-block;">
              View Profile →
            </a>
          </div>
        </div>`).join("")
    : `<p class="subtle">No interviewers found.</p>`;
}

function renderInterviews() {
  let displayInterviews = state.interviews;
  if (state.currentUser && state.currentUser.role === 'INTERVIEWER') {
      displayInterviews = state.interviews.filter(i => i.interviewer_name === state.currentUser.name);
  }

  $("#interviewTable").innerHTML = displayInterviews.length
    ? displayInterviews.map(i => {
        const actions = [];

        if (i.status === "SCHEDULED") {
          if (!i.meeting_link) {
            actions.push(`<button class="secondary-btn" style="padding:5px 10px;font-size:11px" onclick="generateMeeting('${i.interview_id}')">Generate Link</button>`);
          } else {
            actions.push(`<a href="${i.meeting_link}" target="_blank" class="primary-btn" style="padding:5px 10px;font-size:11px;text-decoration:none">Join</a>`);
            actions.push(`<button class="text-btn" style="font-size:11px" onclick="markCompleted('${i.interview_id}')">Mark Done</button>`);
          }
          actions.push(`<button class="text-btn" style="font-size:11px;color:#dc2626" onclick="cancelInterview('${i.interview_id}')">Cancel</button>`);
        }

        if (i.status === "COMPLETED") {
          actions.push(`<button class="secondary-btn" style="padding:5px 10px;font-size:11px" onclick="openFeedback('${i.interview_id}')">Feedback</button>`);
        }

        if (i.status === "CANCELLED" || i.status === "NO_SHOW") {
          actions.push(`<span class="subtle">—</span>`);
        }

        return `<tr>
          <td><strong>${i.candidate_name}</strong><div class="subtle">${i.candidate_skill || "-"}</div></td>
          <td>${i.interviewer_name}</td>
          <td>${formatDate(i.scheduled_date, i.scheduled_time)}</td>
          <td>${i.duration_minutes} min</td>
          <td><span class="badge ${statusClass(i.status)}">${i.status.replace(/_/g, " ")}</span></td>
          <td style="display:flex;gap:6px;flex-wrap:wrap;align-items:center">${actions.join("")}</td>
        </tr>`;
      }).join("")
    : `<tr><td colspan="6" style="text-align:center;color:var(--muted);padding:20px">No interviews scheduled yet.</td></tr>`;
}

function renderFeedbackList() {
  const list = $("#feedbackList");
  if (!list) return;
  
  let completed = state.interviews.filter(i => i.status === "COMPLETED");
  if (state.currentUser && state.currentUser.role === 'INTERVIEWER') {
      completed = completed.filter(i => i.interviewer_name === state.currentUser.name);
  }
  
  list.innerHTML = completed.length
    ? completed.map(i => `
        <div class="interview-row" style="grid-template-columns:1.4fr 1fr auto;cursor:pointer">
          <div><div class="person">${i.candidate_name}</div><div class="subtle">${i.candidate_skill}</div></div>
          <div><div class="subtle">${formatDate(i.scheduled_date, i.scheduled_time)}</div></div>
          <button class="primary-btn" style="padding:6px 12px;font-size:12px" onclick="openFeedback('${i.interview_id}')">Provide / Update Feedback</button>
        </div>`).join("")
    : `<p class="subtle" style="padding:20px 0">No completed interviews yet.</p>`;
}

function updateNavForRole() {
  if (!state.currentUser) return;
  const isInterviewer = state.currentUser.role === 'INTERVIEWER';
  
  if (isInterviewer) {
      // Hide sections an interviewer shouldn't see
      $$(".nav-item[data-section='dashboard']").forEach(e => e.style.display = "none");
      $$(".nav-item[data-section='candidates']").forEach(e => e.style.display = "none");
      $$(".nav-item[data-section='interviewers']").forEach(e => e.style.display = "none");
      $$(".nav-item[data-section='reports']").forEach(e => e.style.display = "none");
      
      // Hide schedule buttons
      if ($("#scheduleBtn")) $("#scheduleBtn").style.display = "none";
      if ($("#scheduleBtn2")) $("#scheduleBtn2").style.display = "none";
      
      showSection("interviews");
  } else {
      // Show all for RECRUITER
      $$(".nav-item").forEach(e => e.style.display = "block");
      if ($("#scheduleBtn")) $("#scheduleBtn").style.display = "block";
      if ($("#scheduleBtn2")) $("#scheduleBtn2").style.display = "block";
  }
}

function renderAll() {
  renderDashboard();
  renderCandidates();
  renderInterviewers();
  renderInterviews();
  renderFeedbackList();
  updateNavForRole();
}

async function loadData() {
  try {
    const [cands, intvs, ivs] = await Promise.all([
      api.getCandidates(),
      api.getInterviewers(),
      api.getInterviews()
    ]);
    state.candidates = cands;
    state.interviewers = intvs;
    state.interviews = ivs;
    renderAll();
  } catch (e) {
    showToast("Failed to load data. Is the backend running?", "error");
  }
}

// ── Navigation ────────────────────────────────────────────────────────────────

function showSection(sectionId) {
  $$(".page-section").forEach(s => s.classList.remove("active-section"));
  const section = $("#" + sectionId);
  if (section) section.classList.add("active-section");
  $$(".nav-item").forEach(b => b.classList.toggle("active", b.dataset.section === sectionId));
  const titles = {
    dashboard: "Interview Dashboard",
    candidates: "Candidates",
    interviewers: "Interviewers",
    interviews: "Interview Management",
    feedback: "Interview Feedback",
    reports: "AI Interview Reports"
  };
  $("#page-title").textContent = titles[sectionId] || "";
}

// ── Schedule Interview Modal ──────────────────────────────────────────────────

function openModal() {
  const eligibleCandidates = state.candidates.filter(c => c.interview_eligible);
  const availableInterviewers = state.interviewers;

  if (!eligibleCandidates.length) {
    showToast("No eligible candidates found.", "error");
    return;
  }

  $("#candidateSelect").innerHTML = eligibleCandidates
    .map(c => `<option value="${c.candidate_id}">${c.name} — ${c.primary_skill || ""}</option>`).join("");

  $("#interviewerSelect").innerHTML = availableInterviewers
    .map(i => `<option value="${i.interviewer_id}" ${i.availability_status !== "AVAILABLE" ? "disabled" : ""}>${i.name} — ${i.expertise || ""}${i.availability_status !== "AVAILABLE" ? " (Busy)" : ""}</option>`).join("");

  const tmrw = new Date();
  tmrw.setDate(tmrw.getDate() + 1);
  $("#dateInput").value = tmrw.toISOString().split("T")[0];
  $("#timeInput").value = "10:30";

  $("#modalBackdrop").classList.add("open");
}

function closeModal() {
  $("#modalBackdrop").classList.remove("open");
}

// ── Add Interviewer Modal ─────────────────────────────────────────────────────

function openAddInterviewerModal() {
  $("#addInterviewerForm").reset();
  $("#addInterviewerBackdrop").classList.add("open");
}

function closeAddInterviewerModal() {
  $("#addInterviewerBackdrop").classList.remove("open");
}

async function submitAddInterviewerForm(e) {
  e.preventDefault();
  const payload = {
    name: $("#aiName").value.trim(),
    email: $("#aiEmail").value.trim(),
    department: $("#aiDept").value.trim(),
    expertise: $("#aiExpertise").value.trim(),
    experience_years: Number($("#aiExp").value) || null,
    availability_status: $("#aiStatus").value
  };

  try {
    await api.createInterviewer(payload);
    showToast(`Interviewer "${payload.name}" added successfully!`, "success");
    closeAddInterviewerModal();
    await loadData();
  } catch (err) {
    showToast(err.message, "error");
  }
}

async function removeInterviewer(id, name) {
  if (!confirm(`Remove interviewer "${name}"?\n\nThis will also delete their user account. This cannot be undone.`)) return;
  try {
    await api.deleteInterviewer(id);
    showToast(`Interviewer "${name}" removed.`, "success");
    await loadData();
  } catch (err) {
    showToast(err.message, "error");
  }
}

async function toggleAvailability(id, currentStatus) {
  const newStatus = currentStatus === "AVAILABLE" ? "BUSY" : "AVAILABLE";
  try {
    await api.updateAvailability(id, newStatus);
    showToast(`Availability updated to ${newStatus}`, "success");
    await loadData();
  } catch (err) {
    showToast(err.message, "error");
  }
}

// ── Interview Actions ──────────────────────────────────────────────────────────

async function generateMeeting(interviewId) {
  try {
    showToast("Generating Jitsi link & sending emails...", "success");
    const result = await api.generateMeeting(interviewId);
    showToast("Meeting created! " + (result.emails?.note || ""), "success");
    await loadData();
  } catch (e) {
    showToast(e.message, "error");
  }
}

async function markCompleted(interviewId) {
  if (!confirm("Mark this interview as Completed?")) return;
  try {
    await api.updateInterviewStatus(interviewId, "COMPLETED");
    showToast("Interview marked as completed.", "success");
    await loadData();
  } catch (e) {
    showToast(e.message, "error");
  }
}

async function cancelInterview(interviewId) {
  if (!confirm("Cancel this interview? This cannot be undone.")) return;
  try {
    await api.deleteInterview(interviewId);
    showToast("Interview cancelled.", "success");
    await loadData();
  } catch (e) {
    showToast(e.message, "error");
  }
}

// ── Feedback & AI ─────────────────────────────────────────────────────────────

let currentFeedbackInterviewId = null;

async function openFeedback(interviewId) {
  currentFeedbackInterviewId = interviewId;
  const iv = state.interviews.find(i => i.interview_id === interviewId);
  if (!iv) return;

  $("#fbCandidateName").textContent = iv.candidate_name;
  showSection("feedback");

  // Pre-populate form if feedback already exists
  try {
    const existing = await api.getFeedback(interviewId);
    if (existing) {
      $("#fTech").value = existing.technical_score ?? "";
      $("#fProb").value = existing.problem_solving_score ?? "";
      $("#fCode").value = existing.coding_score ?? "";
      $("#fComm").value = existing.communication_score ?? "";
      $("#fConf").value = existing.confidence_score ?? "";
      $("#fOver").value = existing.overall_score ?? "";
      $("#fStrengths").value = existing.strengths ?? "";
      $("#fWeak").value = existing.weaknesses ?? "";
      $("#fComments").value = existing.technical_comments ?? "";
      $("#fRec").value = existing.recommendation ?? "HOLD";
    }
  } catch (_) {
    // No existing feedback — form stays empty (fresh submission)
    $("#feedbackForm").reset();
  }
}

async function submitFeedbackForm(e) {
  e.preventDefault();
  if (!currentFeedbackInterviewId) return;

  const iv = state.interviews.find(i => i.interview_id === currentFeedbackInterviewId);

  const data = {
    interviewer_id: iv.interviewer_id,
    technical_score: Number($("#fTech").value),
    problem_solving_score: Number($("#fProb").value),
    communication_score: Number($("#fComm").value),
    coding_score: Number($("#fCode").value),
    confidence_score: Number($("#fConf").value),
    overall_score: Number($("#fOver").value),
    strengths: $("#fStrengths").value,
    weaknesses: $("#fWeak").value,
    technical_comments: $("#fComments").value,
    recommendation: $("#fRec").value
  };

  try {
    await api.submitFeedback(currentFeedbackInterviewId, data);
    showToast("Feedback saved! Running AI analysis...", "success");
    await loadData();
    showSection("reports");
    await runAIAnalysis(currentFeedbackInterviewId);
  } catch (err) {
    showToast(err.message, "error");
  }
}

async function runAIAnalysis(interviewId) {
  const iv = state.interviews.find(i => i.interview_id === interviewId);
  if (!iv) return;

  $("#aiReportContainer").innerHTML = `
    <div style="text-align:center;padding:40px;color:var(--muted)">
      <div style="font-size:32px;margin-bottom:12px">&#8987;</div>
      Running AI Analysis via Gemini... Please wait.
    </div>`;
  showSection("reports");

  try {
    const result = await api.runAIAnalysis(interviewId);

    const badgeClass = result.recommendation === "HIRE" ? "completed" : (result.recommendation === "REJECT" ? "pending" : "scheduled");

    const strengthsHtml = (result.strengths || []).map(s => `<li>${s}</li>`).join("") || "<li>—</li>";
    const gapsHtml = (result.skill_gaps || []).map(s => `<li>${s}</li>`).join("") || "<li>—</li>";
    const risksHtml = (result.risk_factors || []).length
      ? result.risk_factors.map(r => `<li>${r}</li>`).join("")
      : "<li>None identified</li>";

    $("#aiReportContainer").innerHTML = `
      <div class="ai-report-card">
        <div style="display:flex;justify-content:space-between;align-items:flex-start;margin-bottom:20px;flex-wrap:wrap;gap:10px">
          <div>
            <div class="eyebrow">GEMINI AI ANALYSIS</div>
            <h2 style="margin:5px 0">${iv.candidate_name}</h2>
            <div class="subtle">${iv.candidate_skill || "Candidate"} · Interview ID: ${iv.interview_id}</div>
          </div>
          <div style="text-align:right">
            <div style="font-size:34px;font-weight:900;color:var(--primary)">${result.ai_score}/100</div>
            <div class="subtle">AI Match Score</div>
          </div>
        </div>

        <div style="padding:15px;background:var(--bg);border-radius:8px;margin-bottom:20px">
          <strong>Executive Summary</strong>
          <p style="margin:6px 0 0;line-height:1.6;font-size:14px">${result.summary}</p>
        </div>

        <div class="form-row" style="margin-bottom:20px">
          <div>
            <h4 style="margin:0 0 8px">Strengths</h4>
            <ul style="margin:0;padding-left:20px;font-size:13px;color:var(--success);line-height:1.7">${strengthsHtml}</ul>
          </div>
          <div>
            <h4 style="margin:0 0 8px">Skill Gaps</h4>
            <ul style="margin:0;padding-left:20px;font-size:13px;color:var(--warning);line-height:1.7">${gapsHtml}</ul>
          </div>
        </div>

        <div style="margin-bottom:20px">
          <h4 style="margin:0 0 8px">Risk Factors</h4>
          <ul style="margin:0;padding-left:20px;font-size:13px;color:#dc2626;line-height:1.7">${risksHtml}</ul>
        </div>

        <div style="border-top:1px solid var(--line);padding-top:18px;display:flex;justify-content:space-between;align-items:center;flex-wrap:wrap;gap:10px">
          <div>
            <span style="font-weight:700;margin-right:10px">Final Recommendation:</span>
            <span class="badge ${badgeClass}" style="font-size:14px;padding:6px 14px">${result.recommendation}</span>
          </div>
          <div style="font-size:13px;color:var(--muted);max-width:350px">
            <strong>Next Step:</strong> ${result.next_steps}
          </div>
        </div>
      </div>`;

  } catch (e) {
    $("#aiReportContainer").innerHTML = `
      <div class="empty-state">
        <div class="empty-icon">!</div>
        <h3>AI Analysis Failed</h3>
        <p>${e.message}</p>
      </div>`;
  }
}

// ── Event Listeners ───────────────────────────────────────────────────────────

$$(".nav-item").forEach(btn => btn.addEventListener("click", () => showSection(btn.dataset.section)));
$$("[data-section-link]").forEach(btn => btn.addEventListener("click", () => showSection(btn.dataset.sectionLink)));

// Schedule interview modal
$("#scheduleBtn").addEventListener("click", openModal);
$("#scheduleBtn2").addEventListener("click", openModal);
$("#closeModal").addEventListener("click", closeModal);
$("#cancelModal").addEventListener("click", closeModal);
$("#modalBackdrop").addEventListener("click", e => { if (e.target === $("#modalBackdrop")) closeModal(); });

// Add interviewer modal
const addIntvBtn = $("#addInterviewerBtn");
if (addIntvBtn) addIntvBtn.addEventListener("click", openAddInterviewerModal);
const closeAddBtn = $("#closeAddInterviewerModal");
if (closeAddBtn) closeAddBtn.addEventListener("click", closeAddInterviewerModal);
const cancelAddBtn = $("#cancelAddInterviewer");
if (cancelAddBtn) cancelAddBtn.addEventListener("click", closeAddInterviewerModal);
const addIntvBackdrop = $("#addInterviewerBackdrop");
if (addIntvBackdrop) addIntvBackdrop.addEventListener("click", e => { if (e.target === addIntvBackdrop) closeAddInterviewerModal(); });
const addIntvForm = $("#addInterviewerForm");
if (addIntvForm) addIntvForm.addEventListener("submit", submitAddInterviewerForm);

// Schedule interview form
$("#scheduleForm").addEventListener("submit", async (e) => {
  e.preventDefault();
  const payload = {
    candidate_id: $("#candidateSelect").value,
    interviewer_id: $("#interviewerSelect").value,
    interview_type: $("#typeSelect").value || "TECHNICAL",
    scheduled_date: $("#dateInput").value,
    scheduled_time: $("#timeInput").value + ":00",
    duration_minutes: Number($("#durationInput").value)
  };

  try {
    showToast("Scheduling interview...", "success");
    await api.createInterview(payload);
    showToast("Interview scheduled successfully!", "success");
    closeModal();
    await loadData();
    showSection("interviews");
  } catch (err) {
    showToast(err.message, "error");
  }
});

// Feedback form
const fbForm = $("#feedbackForm");
if (fbForm) fbForm.addEventListener("submit", submitFeedbackForm);

// Login form
const loginForm = $("#loginForm");
if (loginForm) {
  loginForm.addEventListener("submit", async (e) => {
    e.preventDefault();
    const email = $("#loginEmail").value.trim();
    const password = $("#loginPassword").value;
    try {
      showToast("Signing in...");
      const user = await api.login(email, password);
      state.currentUser = user;

      // Interviewers have their own dedicated portal
      if (user.role === "INTERVIEWER") {
        window.location.href = "interviewer_profile.html";
        return;
      }
      
      // Update UI
      $("#loginBackdrop").classList.remove("open");
      showToast(`Welcome back, ${user.name}!`, "success");
      
      $("#userInfo").style.display = "block";
      $("#logoutBtn").style.display = "block";
      $("#userNameDisplay").textContent = user.name;
      $("#userRoleDisplay").textContent = user.role;
      
      // Load data
      await loadData();
    } catch (err) {
      showToast(err.message, "error");
    }
  });
}

$("#logoutBtn").addEventListener("click", () => {
    state.currentUser = null;
    $("#loginBackdrop").classList.add("open");
    $("#loginForm").reset();
    $("#userInfo").style.display = "none";
    $("#logoutBtn").style.display = "none";
});

// Do not auto-load data; wait for login.

// ── Auto-Login via URL (for iframe integration) ──
window.addEventListener('DOMContentLoaded', async () => {
  const params = new URLSearchParams(window.location.search);
  const autoEmail = params.get('auto_email');
  const autoRole = params.get('auto_role');
  if (autoEmail && autoRole) {
    state.currentUser = { email: autoEmail, role: autoRole, name: autoEmail.split('@')[0], user_id: 'auto' };
    $("#loginBackdrop")?.classList.remove("open");
    
    if (autoRole === "INTERVIEWER" && !window.location.pathname.includes("interviewer_profile")) {
      window.location.href = "interviewer_profile.html?auto_email=" + encodeURIComponent(autoEmail) + "&auto_role=INTERVIEWER";
      return;
    }

    const uInfo = $("#userInfo");
    if (uInfo) {
      uInfo.style.display = "block";
      $("#logoutBtn").style.display = "block";
      $("#userNameDisplay").textContent = state.currentUser.name;
      $("#userRoleDisplay").textContent = state.currentUser.role;
    }
    
    await loadData();
  }
});
