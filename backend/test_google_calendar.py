from app.services.google_calendar_service import get_calendar_service


service = get_calendar_service()

calendar = service.calendars().get(
    calendarId="primary"
).execute()

print()
print("======================================")
print("Google Calendar connection successful!")
print("======================================")
print()

print("Calendar:")
print(calendar.get("summary"))

print("Calendar ID:")
print(calendar.get("id"))

print()