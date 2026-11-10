"""
email_service.py

Sends interview notification emails via Gmail SMTP.

Requirements:
    - GMAIL_USER       → your Gmail address
    - GMAIL_APP_PASSWORD → 16-char App Password (not your real password)
    - EMAIL_ENABLED=true in .env

When EMAIL_ENABLED=false (default), emails are printed to the console
instead of actually sent — useful for testing without credentials.
"""

import smtplib
from email.message import EmailMessage

from app.config import settings


def _build_candidate_email(
    candidate_name: str,
    candidate_email: str,
    interviewer_name: str,
    interview_date: str,
    interview_time: str,
    duration_minutes: int,
    interview_type: str,
    meeting_link: str,
) -> EmailMessage:
    msg = EmailMessage()
    msg["Subject"] = f"Your {interview_type} Interview is Scheduled — Advanced Hiring System"
    msg["From"] = settings.GMAIL_USER
    msg["To"] = candidate_email

    body = f"""Hi {candidate_name},

Congratulations! Your {interview_type.lower()} interview has been scheduled.

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  Interview Details
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

  Date       : {interview_date}
  Time       : {interview_time}
  Duration   : {duration_minutes} minutes
  Interviewer: {interviewer_name}
  Platform   : Jitsi Meet (no account needed)

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

  Join your interview here:
  {meeting_link}

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Tips:
  • Click the link at your scheduled time
  • No download or account required
  • Join from any browser
  • Ensure your camera and microphone are working

Good luck!

Advanced Hiring System Team
"""
    msg.set_content(body)
    return msg


def _build_interviewer_email(
    interviewer_name: str,
    interviewer_email: str,
    candidate_name: str,
    candidate_skill: str,
    phase1_score: float,
    interview_date: str,
    interview_time: str,
    duration_minutes: int,
    interview_type: str,
    meeting_link: str,
) -> EmailMessage:
    msg = EmailMessage()
    msg["Subject"] = f"Interview Scheduled — {candidate_name} | {interview_type}"
    msg["From"] = settings.GMAIL_USER
    msg["To"] = interviewer_email

    score_str = f"{phase1_score}%" if phase1_score else "N/A"

    body = f"""Hi {interviewer_name},

You have been assigned to conduct a {interview_type.lower()} interview.

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  Interview Details
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

  Candidate     : {candidate_name}
  Technology    : {candidate_skill or 'N/A'}
  Phase 1 Score : {score_str}
  Interview Type: {interview_type}
  Date          : {interview_date}
  Time          : {interview_time}
  Duration      : {duration_minutes} minutes

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

  Join the interview here:
  {meeting_link}

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

After the interview, please submit your feedback through the system
so that the AI analysis and final recommendation can be generated.

Advanced Hiring System Team
"""
    msg.set_content(body)
    return msg


def send_interview_emails(
    candidate_name: str,
    candidate_email: str,
    interviewer_name: str,
    interviewer_email: str,
    candidate_skill: str,
    phase1_score: float,
    interview_date: str,
    interview_time: str,
    duration_minutes: int,
    interview_type: str,
    meeting_link: str,
) -> dict:
    """
    Send interview notification emails to both candidate and interviewer.

    Returns a result dict indicating success/failure for each recipient.
    """
    candidate_msg = _build_candidate_email(
        candidate_name=candidate_name,
        candidate_email=candidate_email,
        interviewer_name=interviewer_name,
        interview_date=interview_date,
        interview_time=interview_time,
        duration_minutes=duration_minutes,
        interview_type=interview_type,
        meeting_link=meeting_link,
    )

    interviewer_msg = _build_interviewer_email(
        interviewer_name=interviewer_name,
        interviewer_email=interviewer_email,
        candidate_name=candidate_name,
        candidate_skill=candidate_skill,
        phase1_score=phase1_score,
        interview_date=interview_date,
        interview_time=interview_time,
        duration_minutes=duration_minutes,
        interview_type=interview_type,
        meeting_link=meeting_link,
    )

    result = {
        "candidate_email_sent": False,
        "interviewer_email_sent": False,
        "note": "",
    }

    if not settings.EMAIL_ENABLED:
        # Print to console for testing when email is disabled
        print("\n" + "="*60)
        print("EMAIL DISABLED — would have sent:")
        print(f"  → Candidate  : {candidate_email}")
        print(f"  → Interviewer: {interviewer_email}")
        print(f"  → Link       : {meeting_link}")
        print("="*60 + "\n")
        result["note"] = "Email disabled (EMAIL_ENABLED=false). Set to true in .env to send real emails."
        return result

    if not settings.GMAIL_USER or not settings.GMAIL_APP_PASSWORD:
        result["note"] = "Email credentials not configured in .env"
        return result

    try:
        with smtplib.SMTP("smtp.gmail.com", 587) as server:
            server.starttls()
            server.login(settings.GMAIL_USER, settings.GMAIL_APP_PASSWORD)

            server.send_message(candidate_msg)
            result["candidate_email_sent"] = True

            server.send_message(interviewer_msg)
            result["interviewer_email_sent"] = True

        result["note"] = "Emails sent successfully"

    except smtplib.SMTPAuthenticationError:
        result["note"] = "Gmail authentication failed. Check GMAIL_USER and GMAIL_APP_PASSWORD in .env"
    except Exception as e:
        result["note"] = f"Email error: {str(e)}"

    return result
