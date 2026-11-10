from app.database import SessionLocal
from app.models.interviewer import Interviewer


db = SessionLocal()

try:

    interviewer = (
        db.query(Interviewer)
        .filter(
            Interviewer.interviewer_id == "INTV-001"
        )
        .first()
    )

    if interviewer:

        print("Interviewer already exists.")
        print(f"ID: {interviewer.interviewer_id}")
        print(f"User ID: {interviewer.user_id}")
        print(f"Status: {interviewer.availability_status}")

    else:

        interviewer = Interviewer(
            interviewer_id="INTV-001",
            user_id="U003",
            department="Engineering",
            experience_years=6,
            expertise="Python, AI, Django",
            availability_status="AVAILABLE"
        )

        db.add(interviewer)

        db.commit()

        print("Interviewer created successfully!")

finally:

    db.close()