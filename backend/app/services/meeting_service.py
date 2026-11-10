"""
meeting_service.py

Generates Jitsi Meet links — completely free, no API key needed.

How Jitsi Meet works:
    Any URL in the form https://meet.jit.si/<room-name> is a valid
    video conference room. Anyone with the link can join immediately
    — no account required.

We generate a room name that is:
  1. Unique per interview
  2. Hard to guess (random suffix)
  3. Human-readable for debugging
"""

import secrets
import string


def generate_meeting_link(interview_id: str, scheduled_date) -> dict:
    """
    Generate a unique Jitsi Meet link for an interview.

    Returns a dict with:
        meeting_id   — the room name (stored in DB)
        meeting_link — the full clickable URL
    """
    # 8-character random alphanumeric suffix — makes link hard to guess
    alphabet = string.ascii_lowercase + string.digits
    random_suffix = "".join(secrets.choice(alphabet) for _ in range(8))

    # Format: AHS-INT-2026-001-20260915-a3f9b2c1
    date_str = str(scheduled_date).replace("-", "")
    clean_id = interview_id.replace(" ", "-")
    room_name = f"AHS-{clean_id}-{date_str}-{random_suffix}"

    meeting_link = f"https://meet.jit.si/{room_name}"

    return {
        "meeting_id": room_name,
        "meeting_link": meeting_link,
    }
