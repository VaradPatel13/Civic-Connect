"""Async Audit Telemetry Aggregator for CivicConnect AI Pipeline.

Buffers agent execution telemetry records in a thread-safe queue and
performs bulk batch inserts to PostgreSQL, preserving database connection pool capacity.
"""

import asyncio
import logging
import queue
import time
from typing import Any, Dict, List, Optional
from sqlalchemy.orm import Session

from backend.models.agent_executions import AgentExecution

logger = logging.getLogger(__name__)


class AsyncAuditBatcher:
    """Thread-safe batch aggregator for agent execution audit logging."""

    def __init__(
        self,
        db_session_factory: Any,
        max_batch_size: int = 100,
        flush_interval_sec: float = 3.0,
    ) -> None:
        self.log_queue: queue.Queue[Dict[str, Any]] = queue.Queue()
        self.session_factory = db_session_factory
        self.max_batch_size = max_batch_size
        self.flush_interval_sec = flush_interval_sec
        self.last_flush = time.time()
        self._flush_task: Optional[asyncio.Task[None]] = None

    def enqueue_audit(self, audit_data: Dict[str, Any]) -> None:
        """Enqueues an agent audit dictionary for background bulk flushing."""
        self.log_queue.put(audit_data)
        if self.log_queue.qsize() >= self.max_batch_size:
            self.flush()

    def flush(self) -> int:
        """Drains up to max_batch_size records from queue and inserts them in one bulk transaction."""
        if self.log_queue.empty():
            return 0

        records_to_insert: List[AgentExecution] = []
        while not self.log_queue.empty() and len(records_to_insert) < self.max_batch_size:
            try:
                log_data = self.log_queue.get_nowait()
                records_to_insert.append(AgentExecution(**log_data))
            except queue.Empty:
                break

        if not records_to_insert:
            return 0

        flushed_count = len(records_to_insert)
        try:
            with self.session_factory() as session:  # type: Session
                session.bulk_save_objects(records_to_insert)
                session.commit()
            logger.info(f"[AuditBatcher] Successfully bulk-committed {flushed_count} agent audit records.")
        except Exception as err:
            logger.error(f"[AuditBatcher] Bulk insert failed ({err}), falling back to single inserts.")
            self._fallback_single_inserts(records_to_insert)

        self.last_flush = time.time()
        return flushed_count

    def _fallback_single_inserts(self, records: List[AgentExecution]) -> None:
        """Individual record fallback insertion if bulk save fails."""
        for rec in records:
            try:
                with self.session_factory() as session:  # type: Session
                    session.add(rec)
                    session.commit()
            except Exception as single_err:
                logger.error(f"[AuditBatcher] Single insert failed for agent {rec.agent_name}: {single_err}")

    async def start_periodic_flush(self) -> None:
        """Starts an async loop flushing audit logs at flush_interval_sec intervals."""
        logger.info(f"[AuditBatcher] Periodic flush loop started (interval={self.flush_interval_sec}s).")
        while True:
            await asyncio.sleep(self.flush_interval_sec)
            try:
                self.flush()
            except Exception as err:
                logger.error(f"[AuditBatcher] Error in periodic flush loop: {err}")
