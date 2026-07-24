from collections.abc import Sequence
from uuid import UUID

from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from backend.models.departments import Department
from backend.models.reports import Ward
from backend.repositories.departments import DepartmentRepository


class DepartmentService:
    def __init__(self, session: AsyncSession):
        self.dept_repo = DepartmentRepository(session)

    async def list_departments(self) -> Sequence[Department]:
        return await self.dept_repo.list_departments()

    async def get_department(self, dept_id: UUID) -> Department:
        dept = await self.dept_repo.get_by_id(dept_id)
        if not dept:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Department not found"
            )
        return dept

    async def list_wards(self) -> Sequence[Ward]:
        return await self.dept_repo.list_wards()
