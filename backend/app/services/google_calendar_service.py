from __future__ import annotations

import os
from datetime import datetime, timedelta

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build


BASE_DIR = os.path.dirname(
    os.path.dirname(
        os.path.dirname(os.path.abspath(__file__))
    )
)

CREDENTIALS_FILE = os.path.join(BASE_DIR, "credentials.json")
TOKEN_FILE = os.path.join(BASE_DIR, "token.json")

SCOPES = [
    "https://www.googleapis.com/auth/calendar"
]


def get_calendar_service():
    """Authenticate and return Google Calendar API service."""

    credentials = None

    if os.path.exists(TOKEN_FILE):
        credentials = Credentials.from_authorized_user_file(
            TOKEN_FILE,
            SCOPES
        )

    if not credentials or not credentials.valid:

        if credentials and credentials.expired and credentials.refresh_token:
            credentials.refresh(Request())

        else:
            if not os.path.exists(CREDENTIALS_FILE):
                raise FileNotFoundError(
                    f"credentials.json not found at: {CREDENTIALS_FILE}"
                )

            flow = InstalledAppFlow.from_client_secrets_file(
                CREDENTIALS_FILE,
                SCOPES
            )

            credentials = flow.run_local_server(port=0)

        with open(TOKEN_FILE, "w") as token:
            token.write(credentials.to_json())

    return build(
        "calendar",
        "v3",
        credentials=credentials
    )


def create_interview_event(
    candidate_name: str,
    candidate_email: str,
    interviewer_name: str,
    interviewer_email: str,
    scheduled_date: str,
    scheduled_time: str,
    duration_minutes: int = 45,
):
    """
    Create a Google Calendar event and request a Google Meet conference.
    """

    start_datetime = datetime.fromisoformat(
        f"{scheduled_date}T{scheduled_time}"
    )

    end_datetime = start_datetime + timedelta(
        minutes=duration_minutes
    )

    service = get_calendar_service()

    event = {
        "summary": f"Technical Interview - {candidate_name}",

        "description": (
            "Advanced Hiring System\n\n"
            f"Candidate: {candidate_name}\n"
            f"Interviewer: {interviewer_name}\n"
            "Interview Type: Technical"
        ),

        "start": {
            "dateTime": start_datetime.isoformat(),
            "timeZone": "Asia/Kolkata",
        },

        "end": {
            "dateTime": end_datetime.isoformat(),
            "timeZone": "Asia/Kolkata",
        },

        "attendees": [
            {
                "email": candidate_email,
            },
            {
                "email": interviewer_email,
            },
        ],

        "conferenceData": {
            "createRequest": {
                "requestId": (
                    f"interview-{int(datetime.now().timestamp())}"
                ),

                "conferenceSolutionKey": {
                    "type": "hangoutsMeet"
                },
            }
        },

        "reminders": {
            "useDefault": True
        },
    }

    created_event = (
        service.events()
        .insert(
            calendarId="primary",
            body=event,
            conferenceDataVersion=1,
            sendUpdates="all",
        )
        .execute()
    )

    return created_event