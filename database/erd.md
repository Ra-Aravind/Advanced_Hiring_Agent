# Phase 2 — Logical ER Diagram

```text
USERS
  │
  ├───────────────┐
  │               │
  ▼               ▼
CANDIDATES     INTERVIEWERS
  │               │
  │               │
  └───────┬───────┘
          │
          ▼
      INTERVIEWS ◄──── USERS (Recruiter)
          │
    ┌─────┼─────────────┐
    ▼     ▼             ▼
PARTICIPANTS  SESSION  FEEDBACK
                           │
                           ▼
                    AI_ANALYSIS

USERS ───────────────► NOTIFICATIONS
USERS ───────────────► AUDIT_LOGS
INTERVIEWS ──────────► NOTIFICATIONS
```

## Main relationships

- One user can have one candidate profile OR one interviewer profile, depending on role.
- One candidate can have many interviews.
- One interviewer can conduct many interviews.
- One recruiter can create/manage many interviews.
- One interview can have multiple participants.
- One interview has one session record in the initial design.
- One interview can have feedback records; normally one final feedback record per interviewer.
- One interview can have one latest AI analysis record.
- Notifications belong to users and can optionally reference an interview.
- Audit logs record important actions performed by users.

## Phase 1 integration

Phase 1 should provide the candidate identity and assessment outcome:

`candidate_id + assessment_id + technology + score + pass/fail + interview_eligible`

Phase 2 should consume that information rather than creating a duplicate candidate record.
