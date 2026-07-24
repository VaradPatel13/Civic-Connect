from collections.abc import Sequence
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.orm import joinedload

from backend.models.departments import Department, DepartmentCategory
from backend.models.reports import Ward


class DepartmentRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def list_departments(self) -> Sequence[Department]:
        stmt = (
            select(Department)
            .options(joinedload(Department.category_links))
            .where(Department.is_active)
        )
        result = await self.session.execute(stmt)
        return result.scalars().unique().all()

    async def get_by_id(self, dept_id: UUID) -> Department | None:
        stmt = (
            select(Department)
            .options(joinedload(Department.category_links))
            .where(Department.id == dept_id)
        )
        result = await self.session.execute(stmt)
        return result.scalars().unique().first()

    async def get_by_code(self, code: str) -> Department | None:
        stmt = (
            select(Department)
            .options(joinedload(Department.category_links))
            .where(Department.code == code)
        )
        result = await self.session.execute(stmt)
        return result.scalars().unique().first()

    async def find_department_for_category(self, category: str) -> Department | None:
        stmt = (
            select(Department)
            .join(DepartmentCategory, Department.id == DepartmentCategory.department_id)
            .where(DepartmentCategory.issue_category == category)
            .where(Department.is_active)
            .limit(1)
        )
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def list_wards(self) -> Sequence[Ward]:
        stmt = select(Ward).where(Ward.is_active).order_by(Ward.ward_number)
        result = await self.session.execute(stmt)
        return result.scalars().all()
