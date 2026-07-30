from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status

from backend.api.deps import get_ai_pipeline_service, get_current_user
from backend.models.citizens import Citizen
from backend.services.ai_pipeline_service import AIPipelineService

router = APIRouter(prefix="/ai", tags=["AI Pipeline"])


@router.post("/process/{report_id}")
async def process_report(
    report_id: UUID,
    current_user: Citizen = Depends(get_current_user),
    service: AIPipelineService = Depends(get_ai_pipeline_service),
):
    result = await service.process_report(report_id)
    if "error" in result:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=result["error"])
    return result

