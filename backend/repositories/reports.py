from collections.abc import Sequence
from urllib.parse import urlparse
from uuid import UUID

from geoalchemy2.elements import WKTElement
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.orm import selectinload

from backend.models.reports import (
    IssueCategory,
    Photo,
    Report,
    ReportStatus,
    StatusLog,
    UrgencyLevel,
)


class ReportRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def create_report(
        self,
        citizen_id: UUID,
        title: str,
        description: str,
        issue_category: IssueCategory,
        urgency: UrgencyLevel = UrgencyLevel.MEDIUM,
        latitude: float | None = None,
        longitude: float | None = None,
        address: str | None = None,
        language: str = "en",
    ) -> Report:
        location = None
        if latitude is not None and longitude is not None:
            location = WKTElement(f"POINT({longitude} {latitude})", srid=4326)

        report = Report(
            citizen_id=citizen_id,
            title=title,
            description=description,
            issue_category=issue_category,
            urgency=urgency,
            latitude=latitude,
            longitude=longitude,
            address=address,
            language=language,
            location=location,
            status=ReportStatus.PENDING,
        )
        self.session.add(report)
        await self.session.flush()

        # Add initial status log
        log = StatusLog(
            report_id=report.id,
            from_status=None,
            to_status=ReportStatus.PENDING,
            changed_by="system",
            reason="Report submitted by citizen",
        )
        self.session.add(log)
        await self.session.commit()
        refreshed = await self.get_by_id(report.id)
        return refreshed or report

    async def get_by_id(self, report_id: UUID) -> Report | None:
        stmt = (
            select(Report)
            .options(
                selectinload(Report.photos),
                selectinload(Report.status_logs),
                selectinload(Report.assignments),
                selectinload(Report.agent_executions),
            )
            .where(Report.id == report_id)
        )
        result = await self.session.execute(stmt)
        return result.scalars().first()

    async def list_reports(
        self,
        citizen_id: UUID | None = None,
        status: ReportStatus | None = None,
        category: IssueCategory | None = None,
        skip: int = 0,
        limit: int = 20,
        include_details: bool = False,
    ) -> Sequence[Report]:
        # Always eagerly load ALL relationships required by ReportResponse to
        # prevent MissingGreenlet errors when SQLAlchemy tries to lazy-load
        # inside an async serialization context.
        stmt = (
            select(Report)
            .options(
                selectinload(Report.photos),
                selectinload(Report.status_logs),
                selectinload(Report.assignments),
                selectinload(Report.agent_executions),
            )
        )
        if citizen_id:
            stmt = stmt.where(Report.citizen_id == citizen_id)
        if status:
            stmt = stmt.where(Report.status == status)
        if category:
            stmt = stmt.where(Report.issue_category == category)

        stmt = stmt.order_by(Report.created_at.desc()).offset(skip).limit(limit)
        result = await self.session.execute(stmt)
        return result.scalars().all()



    async def update_status(
        self,
        report_id: UUID,
        new_status: ReportStatus,
        changed_by: str = "system",
        reason: str | None = None,
    ) -> Report | None:
        report = await self.get_by_id(report_id)
        if not report:
            return None

        old_status = report.status
        report.status = new_status

        log = StatusLog(
            report_id=report.id,
            from_status=old_status,
            to_status=new_status,
            changed_by=changed_by,
            reason=reason,
        )
        self.session.add(log)
        await self.session.commit()
        return await self.get_by_id(report_id)

    async def add_photo(self, report_id: UUID, url: str, public_id: str = "") -> Photo:
        parsed = urlparse(url)
        if parsed.scheme not in ("http", "https") or not parsed.netloc:
            raise ValueError(f"Invalid photo URL format or scheme: '{url}'")

        derived_public_id = public_id or (parsed.path.split("/")[-1] if parsed.path else "photo")
        photo = Photo(
            report_id=report_id,
            cloudinary_url=url,
            public_id=derived_public_id,
        )
        self.session.add(photo)
        await self.session.commit()
        await self.session.refresh(photo)
        return photo

