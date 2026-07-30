"""Reset DB + seed civic reports for development.

Usage:
    python -m backend.scripts.reset_db [--empty] [--seed]

Requires DATABASE_URL env var or .env at project root.
"""
from __future__ import annotations

import argparse
import asyncio
import os
import sys
import uuid
from datetime import UTC, datetime, timedelta
from typing import Any

# Ensure project root is on path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

import bcrypt


async def _hash_password(password: str) -> str:
    return bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")


REPORTS: list[dict[str, Any]] = [
    {
        "title": "Massive pothole at FC Road junction causing accidents",
        "description": (
            "There is a deep pothole approximately 2 feet wide and 6 inches deep "
            "at the FC Road and Ghole Road junction near Symbiosis College. "
            "Multiple two-wheelers have fallen in the last week. "
            "Urgent repair needed before someone gets seriously injured."
        ),
        "category": "roads",
        "status": "open",
        "lat": 18.5167,
        "lng": 73.8563,
        "address": "FC Road, Shivajinagar, Pune, Maharashtra 411004",
        "created_at": datetime.now(UTC) - timedelta(hours=3),
    },
    {
        "title": "Street lights not working on Lambre Road for 2 weeks",
        "description": (
            "All 8 street lights on Lambre Road from Wakade Bridge to Dhankawadi "
            "have been non-functional for nearly 2 weeks. "
            "The area becomes very dark after 8 PM making it unsafe for pedestrians "
            "and enabling anti-social activities. Please repair on priority."
        ),
        "category": "street_lighting",
        "status": "pending",
        "lat": 18.4758,
        "lng": 73.8788,
        "address": "Dhankawadi, Pune, Maharashtra 411043",
        "created_at": datetime.now(UTC) - timedelta(hours=18),
    },
    {
        "title": "Open drainage overflowing on Satara Road near Insurance Nagar",
        "description": (
            "The open drainage channel near Insurance Nagar on Satara Road has been "
            "overflowing for several days causing severe water logging. "
            "This is a health hazard and the smell is unbearable. "
            "Mosquitoes are breeding rapidly. Requesting immediate desilting and repair."
        ),
        "category": "drainage",
        "status": "in_progress",
        "lat": 18.4937,
        "lng": 73.8508,
        "address": "Satara Road, Insurance Nagar, Pune, Maharashtra 411009",
        "created_at": datetime.now(UTC) - timedelta(days=1, hours=5),
    },
]


async def reset_and_seed(seed: bool = True) -> None:
    from sqlalchemy import text
    from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

    import backend.models as _models  # noqa: F401
    from backend.core.config import settings
    from backend.models import Base, Citizen, IssueCategory, Report, ReportStatus, UrgencyLevel

    engine = create_async_engine(settings.database_url, echo=False)
    async_session = async_sessionmaker(engine, expire_on_commit=False)

    print(f"Connecting to: {settings.database_url}")

    # --- WIPE & RECREATE TABLES ---
    print("Dropping all tables...")
    async with engine.begin() as conn:
        await conn.execute(text("DROP SCHEMA public CASCADE"))
        await conn.execute(text("CREATE SCHEMA public"))
    print("Tables dropped.")

    print("Enabling PostGIS extension...")
    async with engine.begin() as conn:
        await conn.execute(text("CREATE EXTENSION IF NOT EXISTS postgis"))
    print("PostGIS enabled.")

    print("Creating schema...")
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    print("Schema created.")

    if not seed:
        print("\nDatabase wiped and reset to clean empty state (no seed data created).")
        await engine.dispose()
        return

    # --- SEED TEST CITIZEN ---
    async with async_session() as session:
        # password: "password123"
        password_hash = await _hash_password("password123")
        citizen = Citizen(
            id=uuid.UUID("00000000-0000-0000-0000-000000000001"),
            display_name="Rahul M.",
            phone="9876543210",
            email="rahul@example.com",
            password_hash=password_hash,
            is_active=True,
            is_verified=True,
        )
        session.add(citizen)
        await session.commit()
        print(f"Created citizen: {citizen.display_name} (ID: {citizen.id})")

    # --- SEED 3 REPORTS ---
    category_map = {
        "roads": IssueCategory.ROADS,
        "street_lighting": IssueCategory.STREET_LIGHTING,
        "drainage": IssueCategory.DRAINAGE,
        "water_supply": IssueCategory.WATER_SUPPLY,
        "waste_management": IssueCategory.WASTE_MANAGEMENT,
        "other": IssueCategory.OTHER,
    }
    status_map = {
        "open": ReportStatus.PENDING,
        "pending": ReportStatus.PENDING,
        "in_progress": ReportStatus.IN_PROGRESS,
        "resolved": ReportStatus.RESOLVED,
    }

    async with async_session() as session:
        for i, r in enumerate(REPORTS, 1):
            cat = category_map.get(str(r["category"]), IssueCategory.OTHER)
            stat = status_map.get(str(r["status"]), ReportStatus.PENDING)

            report = Report(
                id=uuid.UUID(f"00000000-0000-0000-0000-00000000000{i}"),
                citizen_id=citizen.id,
                title=str(r["title"]),
                description=str(r["description"]),
                issue_category=cat,
                status=stat,
                urgency=UrgencyLevel.MEDIUM,
                latitude=float(r["lat"]),
                longitude=float(r["lng"]),
                address=str(r["address"]),
                created_at=r["created_at"],
                updated_at=r["created_at"],
            )
            session.add(report)

        await session.commit()
        print(f"Seeded {len(REPORTS)} reports -> IDs: 000...001, 000...002, 000...003")

    print("\nDone! Database reset and seeded.")
    print("\nTest credentials:")
    print("  Phone:    9876543210")
    print("  Password: password123")
    await engine.dispose()


def main() -> None:
    parser = argparse.ArgumentParser(description="Reset CivicConnect database.")
    parser.add_argument(
        "--empty",
        action="store_true",
        help="Wipe all data and schema without seeding initial test data.",
    )
    parser.add_argument(
        "--seed",
        action="store_true",
        default=True,
        help="Wipe database and seed initial test citizen and reports (default).",
    )

    args = parser.parse_args()
    should_seed = not args.empty

    asyncio.run(reset_and_seed(seed=should_seed))


if __name__ == "__main__":
    main()
