from datetime import UTC, datetime, timedelta
from uuid import UUID

from fastapi import APIRouter, BackgroundTasks, Depends, Header, Query, Response, status
from sqlalchemy import case, func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from backend.api.deps import get_current_user, get_idempotency_service, get_report_service
from backend.core.database import get_db
from backend.models.citizens import Citizen
from backend.models.reports import IssueCategory, Report, ReportStatus
from backend.schemas.reports import ReportCreate, ReportResponse
from backend.services.ai_pipeline_service import run_ai_pipeline_background
from backend.services.idempotency_service import IdempotencyService
from backend.services.report_service import ReportService

router = APIRouter(prefix="/reports", tags=["Reports"])


@router.post("/", response_model=ReportResponse, status_code=status.HTTP_201_CREATED)
async def create_report(
    data: ReportCreate,
    background_tasks: BackgroundTasks,
    response: Response,
    idempotency_key: str | None = Header(None, alias="Idempotency-Key"),
    current_user: Citizen = Depends(get_current_user),
    service: ReportService = Depends(get_report_service),
    idempotency_service: IdempotencyService = Depends(get_idempotency_service),
):
    if idempotency_key:
        is_dup, cached_snapshot, cached_status = await idempotency_service.get_cached_response(
            idempotency_key=idempotency_key, request_data=data
        )
        if is_dup and cached_snapshot is not None:
            response.status_code = cached_status
            return cached_snapshot

    report = await service.create_report(citizen_id=current_user.id, data=data)
    background_tasks.add_task(run_ai_pipeline_background, report.id)
    result = await service.get_report(report.id)

    if idempotency_key:
        await idempotency_service.save_response(
            idempotency_key=idempotency_key,
            request_data=data,
            response_data=result,
            status_code=status.HTTP_201_CREATED,
            report_id=report.id,
        )

    return result


@router.get("/", response_model=list[ReportResponse])
async def list_reports(
    status_filter: ReportStatus | None = Query(None, alias="status"),
    category_filter: IssueCategory | None = Query(None, alias="category"),
    mine_only: bool = Query(False, alias="mine_only"),
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    current_user: Citizen = Depends(get_current_user),
    service: ReportService = Depends(get_report_service),
):
    citizen_id = current_user.id if (mine_only and current_user.role.value == "citizen") else None

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
async def get_dashboard(
    limit: int = Query(10, ge=1, le=50, alias="recent_limit"),
    current_user: Citizen = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    now = datetime.now(UTC)
    month_start = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)

    open_statuses = [
        ReportStatus.PENDING,
        ReportStatus.PROCESSING,
        ReportStatus.VERIFIED,
        ReportStatus.ASSIGNED,
        ReportStatus.IN_PROGRESS,
    ]

    # Consolidated stats query combining total, open, resolved, and avg resolution days (P-02)
    stats_stmt = select(
        func.count(Report.id).label("total_count"),
        func.count(case((Report.status.in_(open_statuses), 1))).label("open_count"),
        func.count(
            case(
                ((Report.status == ReportStatus.RESOLVED) & (Report.resolved_at >= month_start), 1)
            )
        ).label("resolved_month_count"),
        func.avg(
            case(
                (
                    (Report.resolved_at.isnot(None)) & (Report.resolved_at >= month_start),
                    func.extract("day", Report.resolved_at - Report.created_at),
                )
            )
        ).label("avg_days"),
    )
    stats_res = await db.execute(stats_stmt)
    stats_row = stats_res.mappings().first()

    total_count = stats_row["total_count"] if stats_row else 0
    open_count = stats_row["open_count"] if stats_row else 0
    resolved_month_count = stats_row["resolved_month_count"] if stats_row else 0
    avg_resolution_days = (
        round(float(stats_row["avg_days"] or 0), 1)
        if (stats_row and stats_row["avg_days"] is not None)
        else 0.0
    )

    my_reports_stmt = select(func.count(Report.id)).where(Report.citizen_id == current_user.id)
    my_reports_res = await db.execute(my_reports_stmt)
    my_reports_count = my_reports_res.scalar_one_or_none() or 0

    thirty_days_ago = now - timedelta(days=30)
    category_counts = await db.execute(
        select(Report.issue_category, func.count(Report.id).label("cnt"))
        .where(Report.created_at >= thirty_days_ago)
        .group_by(Report.issue_category)
        .order_by(func.count(Report.id).desc())
        .limit(5)
    )
    trending = [
        {
            "label": row.issue_category.value.replace("_", " ").title(),
            "icon": _category_icon(row.issue_category),
            "count": row.cnt,
        }
        for row in category_counts.mappings().all()
    ]

    recent_result = await db.execute(
        select(Report)
        .options(
            selectinload(Report.photos),
            selectinload(Report.agent_executions),
        )
        .order_by(Report.created_at.desc())
        .limit(limit)
    )
    recent_reports = recent_result.scalars().all()

    return {
        "stats": {
            "totalReports": total_count or 0,
            "openReports": open_count or 0,
            "resolvedThisMonth": resolved_month_count or 0,
            "avgResolutionDays": avg_resolution_days,
            "myReports": my_reports_count,
        },
        "recentReports": [_report_to_dict(r) for r in recent_reports],
        "trending": trending,
    }


@router.get("/{report_id}", response_model=ReportResponse)
async def get_report(
    report_id: UUID,
    current_user: Citizen = Depends(get_current_user),
    service: ReportService = Depends(get_report_service),
):
    report = await service.get_report(report_id)
    if current_user.role.value == "citizen" and report.citizen_id != current_user.id:
        from fastapi import HTTPException

        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You do not have authorization to access this report.",
        )
    return report


@router.patch("/{report_id}/status", response_model=ReportResponse)
async def update_report_status(
    report_id: UUID,
    new_status: ReportStatus,
    reason: str | None = None,
    current_user: Citizen = Depends(get_current_user),
    service: ReportService = Depends(get_report_service),
):
    return await service.update_report_status(
        report_id=report_id,
        new_status=new_status,
        changed_by=f"user:{current_user.id}",
        reason=reason,
    )


@router.post("/{report_id}/review", response_model=ReportResponse)
async def review_manual_report(
    report_id: UUID,
    approved: bool = True,
    override_category: IssueCategory | None = None,
    review_notes: str | None = None,
    background_tasks: BackgroundTasks = BackgroundTasks(),
    current_user: Citizen = Depends(get_current_user),
    service: ReportService = Depends(get_report_service),
    db: AsyncSession = Depends(get_db),
):
    """Human-in-the-Loop review endpoint for municipal officers to approve/reject reports."""
    report = await service.get_report(report_id)

    if approved:
        if override_category:
            report.issue_category = override_category
            db.add(report)
            await db.commit()

        await service.update_report_status(
            report_id=report_id,
            new_status=ReportStatus.VERIFIED,
            changed_by=f"officer:{current_user.id}",
            reason=f"Approved by officer: {review_notes or 'Passed manual review'}",
        )
        background_tasks.add_task(run_ai_pipeline_background, report.id)
    else:
        await service.update_report_status(
            report_id=report_id,
            new_status=ReportStatus.REJECTED,
            changed_by=f"officer:{current_user.id}",
            reason=f"Rejected by officer: {review_notes or 'Failed manual review'}",
        )

    return await service.get_report(report_id)


# ── Helpers ──────────────────────────────────────────────────────────────────


def _category_icon(category: IssueCategory) -> str:
    return {
        IssueCategory.ROADS: "alert-circle",
        IssueCategory.WATER_SUPPLY: "water",
        IssueCategory.DRAINAGE: "water-outline",
        IssueCategory.WASTE_MANAGEMENT: "trash",
        IssueCategory.STREET_LIGHTING: "flash",
        IssueCategory.PUBLIC_HEALTH: "medkit",
        IssueCategory.PARKS: "leaf",
        IssueCategory.ENCROACHMENT: "resize",
        IssueCategory.TRAFFIC_INFRASTRUCTURE: "trail-sign",
        IssueCategory.OTHER: "location",
    }.get(category, "location")


def _report_to_dict(report: Report) -> dict:
    return {
        "id": str(report.id),
        "title": report.title,
        "description": report.description,
        "category": _map_category_to_app(report.issue_category),
        "status": _map_status_to_app(report.status),
        "location": {
            "lat": report.latitude,
            "lng": report.longitude,
            "address": report.address,
        },
        "images": (
            [
                {
                    "id": str(p.id),
                    "url": p.cloudinary_url or p.secure_url or "",
                    "display_order": p.display_order,
                    "forensic_score": p.forensic_score,
                    "is_authentic": p.is_authentic,
                }
                for p in sorted(report.photos, key=lambda p: p.display_order or 0)
            ]
            if report.photos
            else []
        ),
        "agentExecutions": (
            [
                {
                    "id": str(ae.id),
                    "agent_name": ae.agent_name,
                    "model_used": ae.model_used,
                    "status": (
                        str(ae.status.value) if hasattr(ae.status, "value") else str(ae.status)
                    ),
                    "confidence": ae.confidence,
                    "execution_ms": ae.execution_ms,
                    "output_snapshot": ae.output_snapshot,
                    "started_at": ae.started_at.isoformat() if ae.started_at else None,
                    "ended_at": ae.ended_at.isoformat() if ae.ended_at else None,
                }
                for ae in getattr(report, "agent_executions", [])
            ]
            if getattr(report, "agent_executions", None)
            else []
        ),
        "authorId": str(report.citizen_id),
        "authorName": "",
        "upvotes": 0,
        "commentCount": 0,
        "isUpvoted": False,
        "createdAt": (
            report.created_at.isoformat() if report.created_at else datetime.now(UTC).isoformat()
        ),
        "updatedAt": (
            report.updated_at.isoformat() if report.updated_at else datetime.now(UTC).isoformat()
        ),
    }


def _map_category_to_app(category: IssueCategory) -> str:
    return {
        IssueCategory.ROADS: "pothole",
        IssueCategory.WATER_SUPPLY: "water",
        IssueCategory.DRAINAGE: "drainage",
        IssueCategory.WASTE_MANAGEMENT: "sanitation",
        IssueCategory.STREET_LIGHTING: "streetlight",
        IssueCategory.PUBLIC_HEALTH: "other",
        IssueCategory.PARKS: "other",
        IssueCategory.ENCROACHMENT: "other",
        IssueCategory.TRAFFIC_INFRASTRUCTURE: "traffic",
        IssueCategory.OTHER: "other",
    }.get(category, "other")


def _map_status_to_app(status: ReportStatus) -> str:
    return {
        ReportStatus.PENDING: "open",
        ReportStatus.PROCESSING: "open",
        ReportStatus.VERIFIED: "open",
        ReportStatus.ASSIGNED: "open",
        ReportStatus.IN_PROGRESS: "in_progress",
        ReportStatus.RESOLVED: "resolved",
        ReportStatus.REJECTED: "rejected",
        ReportStatus.DUPLICATE: "closed",
        ReportStatus.CANCELLED: "closed",
    }.get(status, "open")
