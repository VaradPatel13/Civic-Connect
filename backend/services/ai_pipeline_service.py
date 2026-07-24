from typing import Dict, Any, Optional
from uuid import UUID
import uuid
from sqlalchemy.ext.asyncio import AsyncSession

from backend.repositories.reports import ReportRepository
from backend.repositories.departments import DepartmentRepository
from backend.repositories.agent_executions import AgentExecutionRepository
from backend.models.reports import ReportStatus, UrgencyLevel, IssueCategory, Assignment, AssignmentStatus
from backend.models.agent_executions import AgentStatus

class AIPipelineService:
    """Simulates/executes the AI Multi-Agent orchestration pipeline:

    1. Triage / Content Moderation Agent
    2. Image Forensics Agent
    3. Categorization & Duplicate Detection Agent
    4. Smart Department Routing Agent
    """

    def __init__(self, session: AsyncSession):
        self.session = session
        self.report_repo = ReportRepository(session)
        self.dept_repo = DepartmentRepository(session)
        self.agent_repo = AgentExecutionRepository(session)

    async def process_report(self, report_id: UUID) -> Dict[str, Any]:
        workflow_id = str(uuid.uuid4())
        report = await self.report_repo.get_by_id(report_id)
        if not report:
            return {"error": "Report not found"}

        photo_count = len(report.photos) if report.photos else 0

        # Update report status to PROCESSING
        await self.report_repo.update_status(report_id, ReportStatus.PROCESSING, changed_by="ai_orchestrator")

        # 1. Moderation Agent Execution
        exec_mod = await self.agent_repo.start_execution(
            report_id=report_id,
            workflow_id=workflow_id,
            agent_name="moderation_agent",
            model_used="gemini-1.5-flash",
            input_snapshot={"title": report.title, "description": report.description}
        )
        
        # Simulated moderation check
        is_safe = True
        mod_result = {"flagged": False, "reason": None, "safety_score": 0.98}
        await self.agent_repo.complete_execution(
            execution_id=exec_mod.id,
            status=AgentStatus.COMPLETED if is_safe else AgentStatus.FAILED,
            confidence=0.98,
            output_snapshot=mod_result
        )

        if not is_safe:
            await self.report_repo.update_status(report_id, ReportStatus.REJECTED, changed_by="moderation_agent", reason="Content flagged by AI moderation")
            return {"status": "rejected", "reason": "Content flagged"}

        # 2. Forensics Agent Execution (if photos present)
        forensic_score = 0.95
        if photo_count > 0:
            exec_forensic = await self.agent_repo.start_execution(
                report_id=report_id,
                workflow_id=workflow_id,
                agent_name="image_forensics_agent",
                model_used="claude-3-5-sonnet",
                input_snapshot={"photo_count": photo_count}
            )
            await self.agent_repo.complete_execution(
                execution_id=exec_forensic.id,
                status=AgentStatus.COMPLETED,
                confidence=0.95,
                output_snapshot={"manipulation_detected": False, "authenticity_score": 0.95}
            )

        # 3. Categorization & Duplicate Detection Agent
        exec_cat = await self.agent_repo.start_execution(
            report_id=report_id,
            workflow_id=workflow_id,
            agent_name="categorization_agent",
            model_used="gemini-1.5-pro",
            input_snapshot={"text": report.description}
        )
        
        category_str = report.issue_category.value if hasattr(report.issue_category, "value") else str(report.issue_category)
        await self.agent_repo.complete_execution(
            execution_id=exec_cat.id,
            status=AgentStatus.COMPLETED,
            confidence=0.92,
            output_snapshot={"category": category_str, "urgency": report.urgency.value if hasattr(report.urgency, "value") else str(report.urgency)}
        )

        # 4. Department Routing Agent
        exec_route = await self.agent_repo.start_execution(
            report_id=report_id,
            workflow_id=workflow_id,
            agent_name="routing_agent",
            model_used="gemini-1.5-pro",
            input_snapshot={"category": category_str}
        )

        dept = await self.dept_repo.find_department_for_category(category_str)
        if not dept:
            # Fallback to any department
            depts = await self.dept_repo.list_departments()
            dept = depts[0] if depts else None

        if dept:
            assignment = Assignment(
                report_id=report_id,
                department_id=dept.id,
                status=AssignmentStatus.ACTIVE,
                routing_confidence=0.91,
                routing_reason=f"Matched issue category '{category_str}' to department '{dept.name}'",
                assigned_by="routing_agent"
            )
            self.session.add(assignment)
            await self.session.commit()
            
            await self.report_repo.update_status(report_id, ReportStatus.ASSIGNED, changed_by="routing_agent", reason=f"Assigned to {dept.name}")

        await self.agent_repo.complete_execution(
            execution_id=exec_route.id,
            status=AgentStatus.COMPLETED,
            confidence=0.91,
            output_snapshot={"assigned_department_id": str(dept.id) if dept else None}
        )

        return {
            "workflow_id": workflow_id,
            "status": "completed",
            "report_id": str(report_id),
            "assigned_department": dept.name if dept else None
        }
