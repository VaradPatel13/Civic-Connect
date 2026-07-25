from uuid import UUID
from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload

from backend.api.deps import get_current_user
from backend.core.database import get_db
from backend.models.citizens import Citizen
from backend.models.reports import IssueCategory, Report, ReportStatus
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
    ai_service = AIPipelineService(db)
    await ai_service.process_report(report.id)
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
    citizen_id = current_user.id if current_user.role.value == "citizen" else None
    return await service.list_reports(
        citizen_id=citizen_id,
        status_filter=status_filter,
        category_filter=category_filter,
        skip=skip,
        limit=limit,
    )


# ── PUBLIC DASHBOARD — no auth required ─────────────────────────────────────
# Definitively placed before /{report_id} so FastAPI matches it first.
# (Otherwise "dashboard" gets captured as a UUID and routed to the auth-protected
# GET /{report_id} endpoint, causing 401 Unauthorized.)

@router.get("/dashboard", include_in_schema=False)
async def get_dashboard(db: AsyncSession = Depends(get_db)):
    now = datetime.now(timezone.utc)
    month_start = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)

    total_count = await db.scalar(select(func.count(Report.id)))
    open_count = await db.scalar(
        select(func.count(Report.id)).where(
            Report.status.in_([
                ReportStatus.PENDING, ReportStatus.PROCESSING,
                ReportStatus.VERIFIED, ReportStatus.ASSIGNED,
                ReportStatus.IN_PROGRESS,
            ])
        )
    )
    resolved_month_count = await db.scalar(
        select(func.count(Report.id)).where(Report.status == ReportStatus.RESOLVED)
    )

    avg_result = await db.execute(
        select(
            func.avg(
                func.extract('day', Report.resolved_at - Report.created_at)
            ).label('avg_days')
        ).where(Report.resolved_at.isnot(None), Report.resolved_at >= month_start)
    )
    avg_row = avg_result.mappings().first()
    avg_resolution_days = round(float(avg_row['avg_days'] or 0), 1) if avg_row else 0.0

    thirty_days_ago = now - timedelta(days=30)
    category_counts = await db.execute(
        select(Report.issue_category, func.count(Report.id).label('cnt'))
        .where(Report.created_at >= thirty_days_ago)
        .group_by(Report.issue_category)
        .order_by(func.count(Report.id).desc())
        .limit(5)
    )
    trending = [
        {
            "label": row.issue_category.value.replace("_", " ").title(),
            "icon":  _category_icon(row.issue_category),
            "count": row.cnt,
        }
        for row in category_counts.mappings().all()
    ]

    recent_result = await db.execute(
        select(Report)
        .options(joinedload(Report.photos))
        .order_by(Report.created_at.desc())
        .limit(10)
    )
    recent_reports = recent_result.scalars().unique().all()

    return {
        "stats": {
            "totalReports":       total_count or 0,
            "openReports":        open_count or 0,
            "resolvedThisMonth":  resolved_month_count or 0,
            "avgResolutionDays": avg_resolution_days,
            "myReports":         0,
        },
        "recentReports": [_report_to_dict(r) for r in recent_reports],
        "trending": trending,
    }


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


# ── Helpers ──────────────────────────────────────────────────────────────────

def _category_icon(category: IssueCategory) -> str:
    return {
        IssueCategory.ROADS:                 "alert-circle",
        IssueCategory.WATER_SUPPLY:          "water",
        IssueCategory.DRAINAGE:             "water-outline",
        IssueCategory.WASTE_MANAGEMENT:     "trash",
        IssueCategory.STREET_LIGHTING:      "flash",
        IssueCategory.PUBLIC_HEALTH:        "medkit",
        IssueCategory.PARKS:                "leaf",
        IssueCategory.ENCROACHMENT:         "resize",
        IssueCategory.TRAFFIC_INFRASTRUCTURE: "trail-sign",
        IssueCategory.OTHER:               "location",
    }.get(category, "location")


def _report_to_dict(report: Report) -> dict:
    return {
        "id":          str(report.id),
        "title":       report.title,
        "description": report.description,
        "category":    _map_category_to_app(report.issue_category),
        "status":      _map_status_to_app(report.status),
        "location": {
            "lat":     report.latitude,
            "lng":     report.longitude,
            "address": report.address,
        },
        "images": [
            {
                "id":            str(p.id),
                "url":           p.cloudinary_url,
                "display_order": p.display_order,
                "forensic_score": p.forensic_score,
                "is_authentic":  p.is_authentic,
            }
            for p in sorted(report.photos, key=lambda p: p.display_order)
        ] if report.photos else [],
        "authorId":   str(report.citizen_id),
        "authorName": "",
        "upvotes":     0,
        "commentCount": 0,
        "isUpvoted":  False,
        "createdAt":   report.created_at.isoformat() if report.created_at else datetime.now(timezone.utc).isoformat(),
        "updatedAt":   report.updated_at.isoformat() if report.updated_at else datetime.now(timezone.utc).isoformat(),
    }


def _map_category_to_app(category: IssueCategory) -> str:
    return {
        IssueCategory.ROADS:                   "pothole",
        IssueCategory.WATER_SUPPLY:            "water",
        IssueCategory.DRAINAGE:                "drainage",
        IssueCategory.WASTE_MANAGEMENT:        "sanitation",
        IssueCategory.STREET_LIGHTING:        "streetlight",
        IssueCategory.PUBLIC_HEALTH:          "other",
        IssueCategory.PARKS:                  "other",
        IssueCategory.ENCROACHMENT:           "other",
        IssueCategory.TRAFFIC_INFRASTRUCTURE: "traffic",
        IssueCategory.OTHER:                  "other",
    }.get(category, "other")


def _map_status_to_app(status: ReportStatus) -> str:
    return {
        ReportStatus.PENDING:     "open",
        ReportStatus.PROCESSING:  "open",
        ReportStatus.VERIFIED:    "open",
        ReportStatus.ASSIGNED:    "open",
        ReportStatus.IN_PROGRESS:  "in_progress",
        ReportStatus.RESOLVED:    "resolved",
        ReportStatus.REJECTED:    "rejected",
        ReportStatus.DUPLICATE:   "closed",
        ReportStatus.CANCELLED:   "closed",
    }.get(status, "open")