from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from backend.api.deps import get_current_user
from backend.core.database import get_db
from backend.models.citizens import Citizen
from backend.services.ai_pipeline_service import AIPipelineService

router = APIRouter(prefix="/ai", tags=["AI Pipeline"])


@router.post("/process/{report_id}")
async def process_report(
    report_id: UUID,
    current_user: Citizen = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    service = AIPipelineService(db)
    result = await service.process_report(report_id)
    if "error" in result:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=result["error"])
    return result
