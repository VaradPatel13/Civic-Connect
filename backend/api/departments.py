from typing import List
from uuid import UUID
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from backend.core.database import get_db
from backend.schemas.departments import DepartmentResponse, WardResponse
from backend.services.department_service import DepartmentService

router = APIRouter(prefix="/departments", tags=["Departments"])

@router.get("/", response_model=List[DepartmentResponse])
async def list_departments(db: AsyncSession = Depends(get_db)):
    service = DepartmentService(db)
    return await service.list_departments()

@router.get("/wards", response_model=List[WardResponse])
async def list_wards(db: AsyncSession = Depends(get_db)):
    service = DepartmentService(db)
    return await service.list_wards()

@router.get("/{dept_id}", response_model=DepartmentResponse)
async def get_department(dept_id: UUID, db: AsyncSession = Depends(get_db)):
    service = DepartmentService(db)
    return await service.get_department(dept_id)
