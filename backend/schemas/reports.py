from datetime import datetime
from typing import Any
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

from backend.models.reports import IssueCategory, ReportStatus, UrgencyLevel


class PhotoResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    cloudinary_url: str
    secure_url: str | None = None
    forensic_score: float | None = None
    is_authentic: bool | None = None
    display_order: int

class StatusLogResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    from_status: ReportStatus | None = None
    to_status: ReportStatus
    changed_by: str
    reason: str | None = None

class AssignmentResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    department_id: UUID
    status: str
    assigned_at: datetime
    routing_confidence: float | None = None
    routing_reason: str | None = None

class ReportCreate(BaseModel):
    title: str = Field(..., min_length=3, max_length=255)
    description: str = Field(..., min_length=10)
    issue_category: IssueCategory
    urgency: UrgencyLevel = UrgencyLevel.MEDIUM
    latitude: float | None = None
    longitude: float | None = None
    address: str | None = None
    language: str = "en"
    photos: list[str] = []  # URLs

class ReportUpdate(BaseModel):
    title: str | None = None
    description: str | None = None
    issue_category: IssueCategory | None = None
    urgency: UrgencyLevel | None = None
    status: ReportStatus | None = None
    resolution_notes: str | None = None

class ReportResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    citizen_id: UUID
    ward_id: UUID | None = None
    title: str
    description: str
    language: str
    translated_description: str | None = None
    summary: str | None = None
    issue_category: IssueCategory
    urgency: UrgencyLevel
    status: ReportStatus
    latitude: float | None = None
    longitude: float | None = None
    address: str | None = None
    ward: str | None = None
    zone: str | None = None
    classification_confidence: float | None = None
    moderation_result: dict[str, Any] | None = None
    forensics_result: dict[str, Any] | None = None
    ai_tags: list[str] | None = None
    is_duplicate: bool
    duplicate_of_id: UUID | None = None
    resolution_notes: str | None = None
    resolved_at: datetime | None = None
    created_at: datetime
    updated_at: datetime
    photos: list[PhotoResponse] = []
    status_logs: list[StatusLogResponse] = []
    assignments: list[AssignmentResponse] = []
