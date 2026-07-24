from datetime import datetime
from typing import Optional, List, Dict, Any
from uuid import UUID
from pydantic import BaseModel, Field, ConfigDict
from backend.models.reports import IssueCategory, UrgencyLevel, ReportStatus

class PhotoResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    cloudinary_url: str
    secure_url: Optional[str] = None
    forensic_score: Optional[float] = None
    is_authentic: Optional[bool] = None
    display_order: int

class StatusLogResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    from_status: Optional[ReportStatus] = None
    to_status: ReportStatus
    changed_by: str
    reason: Optional[str] = None

class AssignmentResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    department_id: UUID
    status: str
    assigned_at: datetime
    routing_confidence: Optional[float] = None
    routing_reason: Optional[str] = None

class ReportCreate(BaseModel):
    title: str = Field(..., min_length=3, max_length=255)
    description: str = Field(..., min_length=10)
    issue_category: IssueCategory
    urgency: UrgencyLevel = UrgencyLevel.MEDIUM
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    address: Optional[str] = None
    language: str = "en"
    photos: List[str] = []  # URLs

class ReportUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    issue_category: Optional[IssueCategory] = None
    urgency: Optional[UrgencyLevel] = None
    status: Optional[ReportStatus] = None
    resolution_notes: Optional[str] = None

class ReportResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    citizen_id: UUID
    ward_id: Optional[UUID] = None
    title: str
    description: str
    language: str
    translated_description: Optional[str] = None
    summary: Optional[str] = None
    issue_category: IssueCategory
    urgency: UrgencyLevel
    status: ReportStatus
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    address: Optional[str] = None
    ward: Optional[str] = None
    zone: Optional[str] = None
    classification_confidence: Optional[float] = None
    moderation_result: Optional[Dict[str, Any]] = None
    forensics_result: Optional[Dict[str, Any]] = None
    ai_tags: Optional[List[str]] = None
    is_duplicate: bool
    duplicate_of_id: Optional[UUID] = None
    resolution_notes: Optional[str] = None
    resolved_at: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime
    photos: List[PhotoResponse] = []
    status_logs: List[StatusLogResponse] = []
    assignments: List[AssignmentResponse] = []
