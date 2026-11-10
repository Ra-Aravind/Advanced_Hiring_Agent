# Advanced Hiring System Using AI Agents
## Phase 2 — Complete Progress Package (Steps 1–3)

This package contains everything developed so far for Phase 2.

### Step 1 — Frontend Prototype
Location: `phase-2/`

Includes:
- Interview dashboard
- Candidate management
- Interviewer management
- Interview management
- Schedule interview modal
- Mock Google Meet links
- Interview status tracking
- Feedback placeholder
- Reports placeholder

Run:
- Open `phase-2/index.html` in a browser.

### Step 2 — Database Design
Location: `database/`

Includes:
- `schema.sql`
- `erd.md`
- `sample-data.json`

Tables designed:
- users
- candidates
- interviewers
- interviews
- interview_participants
- interview_sessions
- interview_feedback
- ai_interview_analysis
- notifications
- audit_logs

### Step 3 — API Specification
The current API contract is documented below. This is framework-independent so the team can confirm the backend stack before implementation.

Base path:
`/api/v1`

#### Authentication
- POST `/auth/login`
- POST `/auth/logout`

#### Candidates
- GET `/candidates`
- GET `/candidates/{candidate_id}`

#### Interviewers
- GET `/interviewers`
- GET `/interviewers/{interviewer_id}`
- GET `/interviewers/{interviewer_id}/availability`

#### Interviews
- POST `/interviews`
- GET `/interviews`
- GET `/interviews/{interview_id}`
- PUT `/interviews/{interview_id}`
- DELETE `/interviews/{interview_id}`
- PATCH `/interviews/{interview_id}/status`

#### Meetings
- POST `/meetings/{interview_id}/create`

#### Feedback
- POST `/feedback/{interview_id}`
- GET `/feedback/{interview_id}`

#### AI Analysis
- POST `/ai/{interview_id}/analyze`

#### Notifications
- GET `/notifications/{user_id}`

#### Phase 1 Integration
- POST `/phase1/assessment-result`

### End-to-end Phase 2 workflow

Phase 1 Assessment
→ Candidate Eligibility
→ Interview Scheduling
→ Meeting Link
→ Candidate + Interviewer Notification
→ Google Meet
→ Interview Completion
→ Feedback
→ AI Analysis
→ Interview Report
→ Final Hiring Decision

### Important
Google Meet, authentication, database connectivity, notifications, and AI API
calls are not connected yet. They will be implemented after the team confirms
the backend and database technology.

### Recommended implementation stack
- Frontend: HTML/CSS/JavaScript initially
- Backend: FastAPI
- Database: PostgreSQL
- AI: provider selected by the team
- Meeting: Google Calendar/Google Meet integration
- Authentication: JWT/OAuth as appropriate

Do not treat the mock meeting URLs in the frontend as real Google Meet links.
