# Phase 2 API Specification — v1

## Conventions

- Base URL: `/api/v1`
- JSON request/response bodies
- Authentication required for protected endpoints
- Role-based authorization: ADMIN, RECRUITER, INTERVIEWER, CANDIDATE

## 1. Authentication

### POST /auth/login
Request:
```json
{"email":"user@example.com","password":"password"}
```

Response:
```json
{"access_token":"<token>","token_type":"bearer","user":{"user_id":"U002","role":"RECRUITER"}}
```

### POST /auth/logout
Invalidates the active session/token according to the final auth strategy.

## 2. Candidates

### GET /candidates
Optional filters:
- status
- technology
- phase1_status
- interview_eligible

### GET /candidates/{candidate_id}
Returns profile plus Phase 1 eligibility information.

## 3. Interviewers

### GET /interviewers
Optional filters:
- expertise
- department
- availability_status

### GET /interviewers/{interviewer_id}
Returns interviewer profile.

### GET /interviewers/{interviewer_id}/availability
Returns available time slots.

## 4. Interviews

### POST /interviews
Request:
```json
{
  "candidate_id":"CAND-001",
  "interviewer_id":"INTV-001",
  "recruiter_id":"U002",
  "interview_type":"TECHNICAL",
  "scheduled_date":"2026-09-15",
  "scheduled_time":"10:30",
  "duration_minutes":45,
  "platform":"GOOGLE_MEET"
}
```

### GET /interviews
Supports filters for candidate, interviewer, date, status.

### GET /interviews/{interview_id}
Returns complete interview details.

### PUT /interviews/{interview_id}
Updates schedule/details.

### DELETE /interviews/{interview_id}
Cancels/removes the interview according to business rules.

### PATCH /interviews/{interview_id}/status
Example:
```json
{"status":"COMPLETED"}
```

## 5. Meetings

### POST /meetings/{interview_id}/create
Creates or obtains the external meeting link through the selected integration.

Response:
```json
{
  "interview_id":"INT-1001",
  "platform":"GOOGLE_MEET",
  "meeting_link":"<generated-link>"
}
```

The actual Google API implementation comes later.

## 6. Feedback

### POST /feedback/{interview_id}
Request:
```json
{
  "technical_score":9,
  "problem_solving_score":8,
  "communication_score":9,
  "coding_score":8,
  "confidence_score":9,
  "overall_score":8.6,
  "strengths":"Strong fundamentals",
  "weaknesses":"System design needs improvement",
  "technical_comments":"Good Python knowledge",
  "recommendation":"HIRE"
}
```

### GET /feedback/{interview_id}
Returns submitted feedback.

## 7. AI Analysis

### POST /ai/{interview_id}/analyze
Input is based on interview feedback and available Phase 1 data.

Expected output:
- overall assessment
- strengths
- weaknesses
- skill gaps
- risk factors
- AI score
- recommendation
- summary

The AI output should support human decision-making rather than automatically making an irreversible hiring decision.

## 8. Notifications

### GET /notifications/{user_id}
Returns notifications and reminders for the user.

Future endpoints can include marking notifications as read and retrying failed notifications.

## 9. Phase 1 Integration

### POST /phase1/assessment-result
Expected payload:
```json
{
  "candidate_id":"CAND-001",
  "assessment_id":"ASM-001",
  "technology":"Python",
  "score":84,
  "status":"PASSED",
  "interview_eligible":true
}
```

Phase 2 should consume the Phase 1 candidate identity and result instead of duplicating the entire Phase 1 system.
