-- Advanced Hiring System
-- Phase 2: AI-Powered Interview Management System
-- Logical relational schema; adapt types/syntax to the final DB engine.

CREATE TABLE users (
    user_id VARCHAR(50) PRIMARY KEY,
    name VARCHAR(150) NOT NULL,
    email VARCHAR(255) NOT NULL UNIQUE,
    password_hash TEXT,
    role VARCHAR(30) NOT NULL CHECK (role IN ('ADMIN', 'RECRUITER', 'INTERVIEWER', 'CANDIDATE')),
    phone VARCHAR(30),
    status VARCHAR(20) NOT NULL DEFAULT 'ACTIVE',
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE candidates (
    candidate_id VARCHAR(50) PRIMARY KEY,
    user_id VARCHAR(50) NOT NULL UNIQUE,
    resume_url TEXT,
    experience_years DECIMAL(4,1),
    primary_skill VARCHAR(100),
    phase1_assessment_id VARCHAR(50),
    phase1_score DECIMAL(5,2),
    phase1_status VARCHAR(30),
    interview_eligible BOOLEAN NOT NULL DEFAULT FALSE,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(user_id)
);

CREATE TABLE interviewers (
    interviewer_id VARCHAR(50) PRIMARY KEY,
    user_id VARCHAR(50) NOT NULL UNIQUE,
    department VARCHAR(120),
    experience_years DECIMAL(4,1),
    expertise TEXT,
    availability_status VARCHAR(20) NOT NULL DEFAULT 'AVAILABLE',
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(user_id)
);

CREATE TABLE interviews (
    interview_id VARCHAR(50) PRIMARY KEY,
    candidate_id VARCHAR(50) NOT NULL,
    interviewer_id VARCHAR(50) NOT NULL,
    recruiter_id VARCHAR(50) NOT NULL,
    interview_type VARCHAR(50) NOT NULL DEFAULT 'TECHNICAL',
    scheduled_date DATE NOT NULL,
    scheduled_time TIME NOT NULL,
    duration_minutes INTEGER NOT NULL DEFAULT 45,
    platform VARCHAR(50) NOT NULL DEFAULT 'GOOGLE_MEET',
    meeting_id VARCHAR(255),
    meeting_link TEXT,
    status VARCHAR(30) NOT NULL DEFAULT 'SCHEDULED',
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    started_at TIMESTAMP,
    ended_at TIMESTAMP,
    FOREIGN KEY (candidate_id) REFERENCES candidates(candidate_id),
    FOREIGN KEY (interviewer_id) REFERENCES interviewers(interviewer_id),
    FOREIGN KEY (recruiter_id) REFERENCES users(user_id)
);

CREATE TABLE interview_participants (
    participant_id VARCHAR(50) PRIMARY KEY,
    interview_id VARCHAR(50) NOT NULL,
    user_id VARCHAR(50) NOT NULL,
    participant_role VARCHAR(30) NOT NULL,
    joined_at TIMESTAMP,
    left_at TIMESTAMP,
    FOREIGN KEY (interview_id) REFERENCES interviews(interview_id),
    FOREIGN KEY (user_id) REFERENCES users(user_id)
);

CREATE TABLE interview_sessions (
    session_id VARCHAR(50) PRIMARY KEY,
    interview_id VARCHAR(50) NOT NULL UNIQUE,
    room_id VARCHAR(255),
    started_at TIMESTAMP,
    ended_at TIMESTAMP,
    duration_minutes INTEGER,
    session_status VARCHAR(30) NOT NULL DEFAULT 'NOT_STARTED',
    FOREIGN KEY (interview_id) REFERENCES interviews(interview_id)
);

CREATE TABLE interview_feedback (
    feedback_id VARCHAR(50) PRIMARY KEY,
    interview_id VARCHAR(50) NOT NULL,
    interviewer_id VARCHAR(50) NOT NULL,
    technical_score DECIMAL(4,2) CHECK (technical_score BETWEEN 0 AND 10),
    problem_solving_score DECIMAL(4,2) CHECK (problem_solving_score BETWEEN 0 AND 10),
    communication_score DECIMAL(4,2) CHECK (communication_score BETWEEN 0 AND 10),
    coding_score DECIMAL(4,2) CHECK (coding_score BETWEEN 0 AND 10),
    confidence_score DECIMAL(4,2) CHECK (confidence_score BETWEEN 0 AND 10),
    overall_score DECIMAL(4,2) CHECK (overall_score BETWEEN 0 AND 10),
    strengths TEXT,
    weaknesses TEXT,
    technical_comments TEXT,
    recommendation VARCHAR(30),
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (interview_id) REFERENCES interviews(interview_id),
    FOREIGN KEY (interviewer_id) REFERENCES interviewers(interviewer_id)
);

CREATE TABLE ai_interview_analysis (
    analysis_id VARCHAR(50) PRIMARY KEY,
    interview_id VARCHAR(50) NOT NULL,
    feedback_id VARCHAR(50),
    overall_assessment TEXT,
    strengths TEXT,
    weaknesses TEXT,
    skill_gaps TEXT,
    risk_factors TEXT,
    ai_score DECIMAL(5,2),
    ai_recommendation VARCHAR(30),
    analysis_summary TEXT,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (interview_id) REFERENCES interviews(interview_id),
    FOREIGN KEY (feedback_id) REFERENCES interview_feedback(feedback_id)
);

CREATE TABLE notifications (
    notification_id VARCHAR(50) PRIMARY KEY,
    user_id VARCHAR(50) NOT NULL,
    interview_id VARCHAR(50),
    notification_type VARCHAR(50) NOT NULL,
    message TEXT NOT NULL,
    scheduled_at TIMESTAMP,
    sent_at TIMESTAMP,
    status VARCHAR(20) NOT NULL DEFAULT 'PENDING',
    FOREIGN KEY (user_id) REFERENCES users(user_id),
    FOREIGN KEY (interview_id) REFERENCES interviews(interview_id)
);

CREATE TABLE audit_logs (
    log_id VARCHAR(50) PRIMARY KEY,
    user_id VARCHAR(50),
    action VARCHAR(100) NOT NULL,
    entity_type VARCHAR(50),
    entity_id VARCHAR(50),
    timestamp TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    ip_address VARCHAR(100),
    details TEXT,
    FOREIGN KEY (user_id) REFERENCES users(user_id)
);

-- Recommended indexes
CREATE INDEX idx_interviews_candidate ON interviews(candidate_id);
CREATE INDEX idx_interviews_interviewer ON interviews(interviewer_id);
CREATE INDEX idx_interviews_date_status ON interviews(scheduled_date, status);
CREATE INDEX idx_notifications_user_status ON notifications(user_id, status);
CREATE INDEX idx_audit_logs_entity ON audit_logs(entity_type, entity_id);
