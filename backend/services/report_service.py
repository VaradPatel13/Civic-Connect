from collections.abc import Sequence
from uuid import UUID

from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from backend.models.notifications import NotificationType
from backend.models.reports import IssueCategory, Report, ReportStatus
from backend.models.rewards import RewardReason
from backend.repositories.notifications import NotificationRepository
from backend.repositories.reports import ReportRepository
from backend.repositories.rewards import RewardRepository
from backend.schemas.reports import ReportCreate


class ReportService:
    def __init__(self, session: AsyncSession):
        self.session = session
        self.report_repo = ReportRepository(session)
        self.reward_repo = RewardRepository(session)
        self.notification_repo = NotificationRepository(session)

    async def create_report(self, citizen_id: UUID, data: ReportCreate) -> Report:
        report = await self.report_repo.create_report(
            citizen_id=citizen_id,
            title=data.title,
            description=data.description,
            issue_category=data.issue_category,
            urgency=data.urgency,
            latitude=data.latitude,
            longitude=data.longitude,
            address=data.address,
            language=data.language
        )

        for photo_url in data.photos:
            await self.report_repo.add_photo(report.id, photo_url)

        # Award 50 points for submitting a report
        await self.reward_repo.add_transaction(
            citizen_id=citizen_id,
            points=50,
            reason=RewardReason.REPORT_SUBMISSION,
            description=f"Submitted report '{report.title}'",
            report_id=report.id
        )

        # Create notification
        await self.notification_repo.create_notification(
            citizen_id=citizen_id,
            title="Report Submitted Successfully",
            message=f"Your issue '{report.title}' has been logged and sent for AI processing.",
            notification_type=NotificationType.REPORT_UPDATE,
            report_id=report.id
        )

        return report

    async def get_report(self, report_id: UUID) -> Report:
        report = await self.report_repo.get_by_id(report_id)
        if not report:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Report not found")
        return report

    async def list_reports(
        self,
        citizen_id: UUID | None = None,
        status_filter: ReportStatus | None = None,
        category_filter: IssueCategory | None = None,
        skip: int = 0,
        limit: int = 20
    ) -> Sequence[Report]:
        return await self.report_repo.list_reports(
            citizen_id=citizen_id,
            status=status_filter,
            category=category_filter,
            skip=skip,
            limit=limit
        )

    async def update_report_status(
        self,
        report_id: UUID,
        new_status: ReportStatus,
        changed_by: str = "system",
        reason: str | None = None
    ) -> Report:
        report = await self.report_repo.update_status(report_id, new_status, changed_by, reason)
        if not report:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Report not found")

        # Handle reward points on resolution
        if new_status == ReportStatus.RESOLVED:
            await self.reward_repo.add_transaction(
                citizen_id=report.citizen_id,
                points=100,
                reason=RewardReason.REPORT_RESOLVED,
                description=f"Issue '{report.title}' resolved",
                report_id=report.id
            )

        # Notify citizen
        await self.notification_repo.create_notification(
            citizen_id=report.citizen_id,
            title=f"Report Status Updated to {new_status.name.title()}",
            message=f"Your report '{report.title}' status has changed to {new_status.name.lower()}.",
            notification_type=NotificationType.REPORT_UPDATE,
            report_id=report.id
        )

        return report
