"""
AI Technical Assessment System - FastAPI Application
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
import logging

from app.core.config import settings
from app.core.database import create_tables
from app.api.auth import router as auth_router
from app.api.admin.questions import router as questions_router
from app.api.admin.assessments import router as assessments_router
from app.api.admin.results import router as results_router
from app.api.candidate.sessions import router as candidate_router

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup and shutdown lifecycle."""
    logger.info("🚀 Starting AI Technical Assessment System...")
    await create_tables()
    await _seed_initial_data()
    logger.info("✅ Application ready")
    yield
    logger.info("🛑 Shutting down...")


app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description="AI-powered technical assessment platform for recruitment",
    lifespan=lifespan,
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Routers
app.include_router(auth_router)
app.include_router(questions_router)
app.include_router(assessments_router)
app.include_router(results_router)
app.include_router(candidate_router)


@app.get("/api/health")
async def health():
    return {"status": "ok", "version": settings.APP_VERSION}


async def _seed_initial_data():
    """Seed admin user and technologies if not present."""
    from app.core.database import AsyncSessionLocal
    from app.models.user import User
    from app.models.technology import Technology
    from sqlalchemy import select
    import uuid
    import bcrypt

    async with AsyncSessionLocal() as db:
        try:
            # Seed admin user
            existing_admin = await db.execute(
                select(User).where(User.email == settings.DEFAULT_ADMIN_EMAIL)
            )
            if not existing_admin.scalar_one_or_none():
                # Use bcrypt directly to avoid passlib version conflicts
                raw_password = settings.DEFAULT_ADMIN_PASSWORD.encode('utf-8')
                hashed = bcrypt.hashpw(raw_password, bcrypt.gensalt()).decode('utf-8')
                admin = User(
                    id=str(uuid.uuid4()),
                    email=settings.DEFAULT_ADMIN_EMAIL,
                    hashed_password=hashed,
                    full_name=settings.DEFAULT_ADMIN_NAME,
                    role="admin",
                )
                db.add(admin)
                logger.info(f"✅ Admin user created: {settings.DEFAULT_ADMIN_EMAIL}")

            # Seed technologies
            technologies = [
                {"name": "Python", "slug": "python", "icon": "🐍", "color": "#3776AB"},
                {"name": "Java", "slug": "java", "icon": "☕", "color": "#ED8B00"},
                {"name": "C", "slug": "c", "icon": "⚙️", "color": "#A8B9CC"},
                {"name": "C++", "slug": "cpp", "icon": "🔧", "color": "#00599C"},
                {"name": "HTML", "slug": "html", "icon": "🌐", "color": "#E34F26"},
                {"name": "CSS", "slug": "css", "icon": "🎨", "color": "#1572B6"},
                {"name": "Power BI", "slug": "powerbi", "icon": "📊", "color": "#F2C811"},
            ]

            for tech_data in technologies:
                existing = await db.execute(
                    select(Technology).where(Technology.slug == tech_data["slug"])
                )
                if not existing.scalar_one_or_none():
                    tech = Technology(
                        id=str(uuid.uuid4()),
                        **tech_data,
                    )
                    db.add(tech)
                    logger.info(f"✅ Technology seeded: {tech_data['name']}")

            await db.commit()
        except Exception as e:
            logger.error(f"Seed error: {e}")
            await db.rollback()
