from datetime import datetime, date, time, timedelta

from sqlalchemy.orm import Session

from app.models.interview import Interview


def has_schedule_conflict(
    db: Session,
    interviewer_id: str,
    scheduled_date: date,
    scheduled_time: time,
    duration_minutes: int,
) -> bool:

    # New interview start and end time
    new_start = datetime.combine(
        scheduled_date,
        scheduled_time
    )

    new_end = (
        new_start
        + timedelta(minutes=duration_minutes)
    )

    # Get active interviews for this interviewer
    # on the same date
    existing_interviews = (
        db.query(Interview)
        .filter(
            Interview.interviewer_id == interviewer_id,
            Interview.scheduled_date == scheduled_date,
            Interview.status.in_([
                "SCHEDULED",
                "IN_PROGRESS"
            ])
        )
        .all()
    )

    for interview in existing_interviews:

        existing_start = datetime.combine(
            interview.scheduled_date,
            interview.scheduled_time
        )

        existing_end = (
            existing_start
            + timedelta(
                minutes=interview.duration_minutes
            )
        )

        # Check actual time overlap
        if (
            new_start < existing_end
            and new_end > existing_start
        ):
            return True

    return False