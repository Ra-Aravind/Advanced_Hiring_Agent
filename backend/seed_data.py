"""
seed_data.py — Populate the database with realistic test data.

Run once from the backend/ directory:
    python seed_data.py

Safe to run multiple times — skips rows that already exist
and removes junk rows created during early testing.
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.database import SessionLocal
from app.models.user import User
from app.models.candidate import Candidate
from app.models.interviewer import Interviewer
from app.models.interview import Interview


def seed():
    db = SessionLocal()

    try:
        # ── 1. Remove junk rows from early testing ────────────────
        junk_candidate = db.get(Candidate, "string")
        if junk_candidate:
            db.delete(junk_candidate)

        # Remove orphan interviews that point to missing candidates
        all_interviews = db.query(Interview).all()
        for iv in all_interviews:
            cand = db.get(Candidate, iv.candidate_id)
            if not cand or iv.candidate_id == "string":
                db.delete(iv)

        db.commit()
        print("OK Removed junk rows")

        # ── 2. Users ──────────────────────────────────────────────
        DEFAULT_PASSWORD = "password123"

        users = [
            User(user_id="U-REC-01",   name="Admin Recruiter",  email="recruiter@hiringco.com",       role="RECRUITER",    status="ACTIVE", password_hash=DEFAULT_PASSWORD),
            User(user_id="U-CAND-01",  name="John Doe",         email="john.doe@email.com",           role="CANDIDATE",    status="ACTIVE", password_hash=DEFAULT_PASSWORD),
            User(user_id="U-CAND-02",  name="Priya Kumar",      email="priya.kumar@email.com",        role="CANDIDATE",    status="ACTIVE", password_hash=DEFAULT_PASSWORD),
            User(user_id="U-CAND-03",  name="Alex Smith",       email="alex.smith@email.com",         role="CANDIDATE",    status="ACTIVE", password_hash=DEFAULT_PASSWORD),
            User(user_id="U-CAND-04",  name="Meera Raj",        email="meera.raj@email.com",          role="CANDIDATE",    status="ACTIVE", password_hash=DEFAULT_PASSWORD),
            User(user_id="U-INTV-01",  name="Rahul Sharma",     email="rahul.sharma@hiringco.com",    role="INTERVIEWER",  status="ACTIVE", password_hash=DEFAULT_PASSWORD),
            User(user_id="U-INTV-02",  name="Priya Patel",      email="priya.patel@hiringco.com",     role="INTERVIEWER",  status="ACTIVE", password_hash=DEFAULT_PASSWORD),
            User(user_id="U-INTV-03",  name="Arun Kumar",       email="arun.kumar@hiringco.com",      role="INTERVIEWER",  status="ACTIVE", password_hash=DEFAULT_PASSWORD),
            User(user_id="U-INTV-04",  name="Divya Menon",      email="divya.menon@hiringco.com",     role="INTERVIEWER",  status="ACTIVE", password_hash=DEFAULT_PASSWORD),
        ]

        for u in users:
            existing = db.get(User, u.user_id)
            if not existing:
                db.add(u)
                print(f"  + User  {u.user_id}  {u.name}")
            else:
                existing.password_hash = DEFAULT_PASSWORD
                print(f"  ~ User  {u.user_id}  updated password")

        db.commit()

        # ── 3. Candidates ─────────────────────────────────────────
        candidates = [
            Candidate(
                candidate_id="CAND-001", user_id="U-CAND-01",
                primary_skill="Python",
                phase1_assessment_id="ASM-001", phase1_score=84.0,
                phase1_status="PASSED", interview_eligible=True,
                experience_years=2.5,
            ),
            Candidate(
                candidate_id="CAND-002", user_id="U-CAND-02",
                primary_skill="Java",
                phase1_assessment_id="ASM-002", phase1_score=91.0,
                phase1_status="PASSED", interview_eligible=True,
                experience_years=3.0,
            ),
            Candidate(
                candidate_id="CAND-003", user_id="U-CAND-03",
                primary_skill="C++",
                phase1_assessment_id="ASM-003", phase1_score=62.0,
                phase1_status="FAILED", interview_eligible=False,
                experience_years=1.0,
            ),
            Candidate(
                candidate_id="CAND-004", user_id="U-CAND-04",
                primary_skill="Power BI",
                phase1_assessment_id="ASM-004", phase1_score=88.0,
                phase1_status="PASSED", interview_eligible=True,
                experience_years=4.0,
            ),
        ]

        for c in candidates:
            existing = db.get(Candidate, c.candidate_id)
            if not existing:
                db.add(c)
                print(f"  + Candidate  {c.candidate_id}  ({c.primary_skill})")
            else:
                # Update eligibility if it was wrong
                existing.interview_eligible = c.interview_eligible
                existing.user_id = c.user_id
                existing.primary_skill = c.primary_skill
                existing.phase1_score = c.phase1_score
                existing.phase1_status = c.phase1_status
                print(f"  · Candidate  {c.candidate_id}  updated")

        db.commit()

        # ── 4. Interviewers ───────────────────────────────────────
        interviewers = [
            Interviewer(
                interviewer_id="INTV-001", user_id="U-INTV-01",
                department="Engineering",
                expertise="Python, AI, Django, Machine Learning",
                availability_status="AVAILABLE", experience_years=6.0,
            ),
            Interviewer(
                interviewer_id="INTV-002", user_id="U-INTV-02",
                department="Engineering",
                expertise="Java, Spring Boot, Microservices, REST APIs",
                availability_status="AVAILABLE", experience_years=5.0,
            ),
            Interviewer(
                interviewer_id="INTV-003", user_id="U-INTV-03",
                department="Systems",
                expertise="C++, Systems Programming, Algorithms, Data Structures",
                availability_status="BUSY", experience_years=8.0,
            ),
            Interviewer(
                interviewer_id="INTV-004", user_id="U-INTV-04",
                department="Analytics",
                expertise="Power BI, SQL, Data Analytics, Tableau",
                availability_status="AVAILABLE", experience_years=4.0,
            ),
        ]

        for i in interviewers:
            existing = db.get(Interviewer, i.interviewer_id)
            if not existing:
                db.add(i)
                print(f"  + Interviewer  {i.interviewer_id}  ({i.availability_status})")
            else:
                existing.user_id = i.user_id
                existing.department = i.department
                existing.expertise = i.expertise
                existing.experience_years = i.experience_years
                print(f"  · Interviewer  {i.interviewer_id}  updated")

        db.commit()

        # ── 5. Interviews ─────────────────────────────────────────
        from datetime import date, time

        interviews = [
            Interview(
                interview_id="INT-2026-001",
                candidate_id="CAND-001", interviewer_id="INTV-001",
                recruiter_id="U-REC-01", interview_type="TECHNICAL",
                scheduled_date=date(2026, 9, 15), scheduled_time=time(10, 30, 0),
                duration_minutes=45, platform="JITSI_MEET",
                meeting_link="https://meet.jit.si/AHS-INT-2026-001-demo",
                status="SCHEDULED",
            ),
            Interview(
                interview_id="INT-2026-002",
                candidate_id="CAND-002", interviewer_id="INTV-002",
                recruiter_id="U-REC-01", interview_type="TECHNICAL",
                scheduled_date=date(2026, 9, 15), scheduled_time=time(12, 0, 0),
                duration_minutes=45, platform="JITSI_MEET",
                meeting_link="https://meet.jit.si/AHS-INT-2026-002-demo",
                status="SCHEDULED",
            ),
            Interview(
                interview_id="INT-2026-003",
                candidate_id="CAND-004", interviewer_id="INTV-004",
                recruiter_id="U-REC-01", interview_type="HR",
                scheduled_date=date(2026, 9, 10), scheduled_time=time(15, 30, 0),
                duration_minutes=60, platform="JITSI_MEET",
                meeting_link="https://meet.jit.si/AHS-INT-2026-003-demo",
                status="COMPLETED",
            ),
        ]

        for iv in interviews:
            existing = db.get(Interview, iv.interview_id)
            if not existing:
                db.add(iv)
                print(f"  + Interview  {iv.interview_id}  ({iv.status})")
            else:
                print(f"  · Interview  {iv.interview_id}  already exists")

        db.commit()
        print("\nSUCCESS: Seed complete!")

    except Exception as e:
        db.rollback()
        print(f"\nERROR: Seed failed: {e}")
        raise
    finally:
        db.close()


if __name__ == "__main__":
    seed()
