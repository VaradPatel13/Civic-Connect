from collections.abc import Sequence
from datetime import UTC, datetime
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from backend.models.agent_executions import AgentExecution, AgentStatus


class AgentExecutionRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def start_execution(
        self,
        report_id: UUID,
        agent_name: str,
        workflow_id: str | None = None,
        model_used: str | None = None,
        input_snapshot: dict | None = None
    ) -> AgentExecution:
        execution = AgentExecution(
            report_id=report_id,
            workflow_id=workflow_id,
            agent_name=agent_name,
            model_used=model_used,
            status=AgentStatus.RUNNING,
            input_snapshot=input_snapshot,
            started_at=datetime.now(UTC)
        )
        self.session.add(execution)
        await self.session.commit()
        await self.session.refresh(execution)
        return execution

    async def complete_execution(
        self,
        execution_id: UUID,
        status: AgentStatus = AgentStatus.COMPLETED,
        confidence: float | None = None,
        output_snapshot: dict | None = None,
        error_snapshot: dict | None = None,
        execution_ms: int | None = None
    ) -> AgentExecution | None:
        stmt = select(AgentExecution).where(AgentExecution.id == execution_id)
        result = await self.session.execute(stmt)
        execution = result.scalar_one_or_none()
        if not execution:
            return None

        execution.status = status
        execution.confidence = confidence
        execution.output_snapshot = output_snapshot
        execution.error_snapshot = error_snapshot
        execution.ended_at = datetime.now(UTC)
        if execution.started_at:
            delta = execution.ended_at - execution.started_at
            execution.execution_ms = execution_ms or int(delta.total_seconds() * 1000)

        await self.session.commit()
        await self.session.refresh(execution)
        return execution

    async def get_by_report(self, report_id: UUID) -> Sequence[AgentExecution]:
        stmt = select(AgentExecution).where(AgentExecution.report_id == report_id).order_by(AgentExecution.started_at.desc())
        result = await self.session.execute(stmt)
        return result.scalars().all()
