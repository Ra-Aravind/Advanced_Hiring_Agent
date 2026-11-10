from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
import os

from app.database import Base, engine
from app.models import User, Candidate, Interviewer, Interview, InterviewFeedback

from app.routes import (
    candidates,
    interviewers,
    interviews,
    meetings,
    feedback,
    ai_analysis,
    phase1_integration,
    auth,
)
from app.routes.interviewer_profile import router as interviewer_profile_router


# Create all tables
Base.metadata.create_all(bind=engine)


app = FastAPI(
    title="Advanced Hiring System — Phase 2",
    description="AI-Powered Interview Management System",
    version="2.0.0",
)


# ── CORS ──────────────────────────────────────────────────────
# allow_origins=["*"] + allow_credentials=True is INVALID (browser blocks it).
# We list every local origin explicitly so both file:// and localhost work.
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://127.0.0.1:5173",
        "http://localhost:3000",
        "http://127.0.0.1:3000",
        "http://localhost:8000",
        "http://127.0.0.1:8000",
        "http://localhost:8001",
        "http://127.0.0.1:8001",
        "null",           # file:// pages send Origin: null
    ],
    allow_credentials=False,  # no cookies needed — session is in JS memory
    allow_methods=["*"],
    allow_headers=["*"],
)


# ── Routers ───────────────────────────────────────────────────
app.include_router(auth.router,                    prefix="/api/v1/auth",                tags=["Auth"])
app.include_router(candidates.router,              prefix="/api/v1/candidates",          tags=["Candidates"])
app.include_router(interviewers.router,            prefix="/api/v1/interviewers",        tags=["Interviewers"])
app.include_router(interviewer_profile_router,     prefix="/api/v1/interviewers",        tags=["Interviewer Profile"])
app.include_router(interviews.router,              prefix="/api/v1/interviews",          tags=["Interviews"])
app.include_router(meetings.router,            prefix="/api/v1/meetings",            tags=["Meetings"])
app.include_router(feedback.router,            prefix="/api/v1/feedback",            tags=["Feedback"])
app.include_router(ai_analysis.router,         prefix="/api/v1/ai",                  tags=["AI Analysis"])
app.include_router(phase1_integration.router,  prefix="/api/v1/phase1",              tags=["Phase 1 Integration"])


@app.get("/")
def root():
    return {
        "message": "Advanced Hiring System API",
        "phase": "Phase 2 — Interview Management",
        "status": "running",
        "docs": "/docs",
    }


@app.get("/health")
def health():
    return {"status": "ok"}

# Serve Phase 2 frontend statically
frontend_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "phase-2")
if os.path.exists(frontend_path):
    app.mount("/app", StaticFiles(directory=frontend_path, html=True), name="frontend")