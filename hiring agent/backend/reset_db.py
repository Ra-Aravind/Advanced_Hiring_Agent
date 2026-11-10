import asyncio
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.core.database import drop_tables
from seed_data.seed import seed_questions

async def main():
    print("Dropping all tables...")
    await drop_tables()
    print("Tables dropped. Seeding...")
    await seed_questions()
    print("Seeding complete.")

if __name__ == "__main__":
    asyncio.run(main())
