from uuid import UUID

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from backend.api.deps import get_current_user
from backend.core.database import get_db
from backend.models.citizens import Citizen
from backend.models.reports import IssueCategory, ReportStatus
from backend.schemas.reports import ReportCreate, ReportResponse
from backend.services.ai_pipeline_service import AIPipelineService
from backend.services.report_service import ReportService

router = APIRouter(prefix="/reports", tags=["Reports"])


@router.post("/", response_model=ReportResponse, status_code=status.HTTP_201_CREATED)
async def create_report(
    data: ReportCreate,
    current_user: Citizen = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    service = ReportService(db)
    report = await service.create_report(citizen_id=current_user.id, data=data)

    # Trigger background AI processing pipeline asynchronously
    ai_service = AIPipelineService(db)
    await ai_service.process_report(report.id)

    # Reload report with updated status and assignments
    return await service.get_report(report.id)


@router.get("/", response_model=list[ReportResponse])
async def list_reports(
    status_filter: ReportStatus | None = Query(None, alias="status"),
    category_filter: IssueCategory | None = Query(None, alias="category"),
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    current_user: Citizen = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    service = ReportService(db)
    # If citizen, only list their reports unless admin
    citizen_id = current_user.id if current_user.role.value == "citizen" else None
    return await service.list_reports(
        citizen_id=citizen_id,
        status_filter=status_filter,
        category_filter=category_filter,
        skip=skip,
        limit=limit,
    )


@router.get("/{report_id}", response_model=ReportResponse)
async def get_report(
    report_id: UUID,
    current_user: Citizen = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    service = ReportService(db)
    return await service.get_report(report_id)


@router.patch("/{report_id}/status", response_model=ReportResponse)
async def update_report_status(
    report_id: UUID,
    new_status: ReportStatus,
    reason: str | None = None,
    current_user: Citizen = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    service = ReportService(db)
    return await service.update_report_status(
        report_id=report_id,
        new_status=new_status,
        changed_by=f"user:{current_user.id}",
        reason=reason,
    )
