from uuid import UUID

from fastapi import APIRouter, Depends

from backend.api.deps import get_current_user, get_department_service
from backend.models.citizens import Citizen
from backend.schemas.departments import DepartmentResponse, WardResponse
from backend.services.department_service import DepartmentService

router = APIRouter(prefix="/departments", tags=["Departments"])


@router.get("/", response_model=list[DepartmentResponse])
async def list_departments(
    current_user: Citizen = Depends(get_current_user),
    service: DepartmentService = Depends(get_department_service),
):
    return await service.list_departments()


@router.get("/wards", response_model=list[WardResponse])
async def list_wards(
    current_user: Citizen = Depends(get_current_user),
    service: DepartmentService = Depends(get_department_service),
):
    return await service.list_wards()


@router.get("/{dept_id}", response_model=DepartmentResponse)
async def get_department(
    dept_id: UUID,
    current_user: Citizen = Depends(get_current_user),
    service: DepartmentService = Depends(get_department_service),
):
    return await service.get_department(dept_id)


