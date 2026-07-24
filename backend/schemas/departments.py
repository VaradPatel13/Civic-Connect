from typing import Optional, List
from uuid import UUID
from datetime import datetime
from pydantic import BaseModel, ConfigDict

class CategoryResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    issue_category: str
    is_primary: bool

class DepartmentResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    code: str
    name: str
    description: Optional[str] = None
    category: str
    contact_email: Optional[str] = None
    contact_phone: Optional[str] = None
    operating_hours: Optional[str] = None
    sla_low_days: int
    sla_medium_days: int
    sla_high_hours: int
    sla_critical_hours: int
    active_report_count: int
    weekly_capacity: Optional[int] = None
    is_active: bool
    created_at: datetime
    category_links: List[CategoryResponse] = []

class WardResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    ward_name: str
    ward_number: int
    zone: str
    is_active: bool
