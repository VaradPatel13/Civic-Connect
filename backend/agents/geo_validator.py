"""Geo-Validation Agent for CivicConnect.

Validates citizen report GPS coordinates (latitude, longitude) against official PMC
administrative ward boundary geometries using PostGIS ST_Covers spatial joins.

Specs: docs/specs/ai-pipeline.md, docs/specs/AGENT.md
"""

from __future__ import annotations

import asyncio
import logging
import time
from typing import Any, TypedDict

from sqlalchemy import text

from backend.agents.state import GeoValidationResult, PipelineSharedState

logger = logging.getLogger(__name__)


class PMCBoundaryDict(TypedDict):
    ward_id: str
    ward_name: str
    zone_name: str
    min_lat: float
    max_lat: float
    min_lon: float
    max_lon: float


# Pune Municipal Corporation (PMC) ward boundary polygon lookups
PUNE_PMC_BOUNDARIES: list[PMCBoundaryDict] = [
    {"ward_id": "WARD_01", "ward_name": "Aundh-Baner", "zone_name": "Zone 1", "min_lat": 18.54, "max_lat": 18.58, "min_lon": 73.78, "max_lon": 73.83},
    {"ward_id": "WARD_02", "ward_name": "Kothrud-Bavdhan", "zone_name": "Zone 1", "min_lat": 18.49, "max_lat": 18.53, "min_lon": 73.79, "max_lon": 73.83},
    {"ward_id": "WARD_03", "ward_name": "Shivajinagar-Ghole Road", "zone_name": "Zone 2", "min_lat": 18.51, "max_lat": 18.54, "min_lon": 73.83, "max_lon": 73.86},
    {"ward_id": "WARD_04", "ward_name": "Kasba-Vishrambaug Wada", "zone_name": "Zone 2", "min_lat": 18.50, "max_lat": 18.52, "min_lon": 73.84, "max_lon": 73.87},
    {"ward_id": "WARD_05", "ward_name": "Hadapsar-Mundhwa", "zone_name": "Zone 3", "min_lat": 18.48, "max_lat": 18.53, "min_lon": 73.90, "max_lon": 73.96},
]


class GeoValidationAgent:
    """Agent that performs spatial boundary matching over report coordinates."""

    def __init__(self, db_session_factory: Any | None = None) -> None:
        self.db_session_factory = db_session_factory

    async def process(self, state: PipelineSharedState) -> dict[str, Any]:
        """Executes Geo Validation node logic for LangGraph workflow asynchronously (P-01)."""
        start_time = time.time()
        raw_payload = state.get("raw_payload", {})

        latitude = raw_payload.get("latitude")
        longitude = raw_payload.get("longitude")

        if latitude is None or longitude is None:
            logger.warning("[GeoValidator] Report missing latitude/longitude coordinates.")
            result = self._build_fallback(reason="Missing GPS coordinates")
            return {"agent_outputs": {"geo_validation": result}}

        try:
            lat = float(latitude)
            lon = float(longitude)
        except (ValueError, TypeError):
            logger.warning(f"[GeoValidator] Invalid coordinate format: lat={latitude}, lon={longitude}")
            result = self._build_fallback(reason="Invalid numeric coordinates")
            return {"agent_outputs": {"geo_validation": result}}

        # Pune Regional Coordinate Envelope Check (Zero-Hallucination Guard)
        if not (18.0 <= lat <= 19.0 and 73.0 <= lon <= 74.5):
            logger.warning(f"[GeoValidator] Coordinates ({lat}, {lon}) outside Pune metropolitan area limits.")
            result = self._build_fallback(reason="Coordinates outside Pune regional boundary")
            return {"agent_outputs": {"geo_validation": result}}

        # Attempt PostGIS spatial query if database session factory is provided
        if self.db_session_factory is not None:
            spatial_match = await self._query_postgis_ward(lat, lon)
            if spatial_match:
                logger.info(f"[GeoValidator] PostGIS ST_Covers matched ward '{spatial_match['ward_name']}'.")
                return {"agent_outputs": {"geo_validation": spatial_match}}

        # Deterministic spatial lookup fallback using PMC boundary bounding boxes
        result = self._query_pmc_bounding_box(lat, lon)
        execution_ms = (time.time() - start_time) * 1000.0
        logger.info(f"[GeoValidator] Geo-validation completed in {execution_ms:.2f}ms. Matched: {result.get('boundary_matched')}")

        return {"agent_outputs": {"geo_validation": result}}

    async def _query_postgis_ward(self, lat: float, lon: float) -> GeoValidationResult | None:
        """Queries PostGIS database using ST_Covers over jurisdiction geometry asynchronously (P-01)."""
        factory = self.db_session_factory
        if factory is None:
            return None

        try:
            query = text("""
                SELECT code, name, category
                FROM departments
                WHERE jurisdiction_geometry IS NOT NULL
                AND ST_Covers(jurisdiction_geometry, ST_SetSRID(ST_MakePoint(:lon, :lat), 4326))
                LIMIT 1;
            """)
            session_ctx = factory()
            row = None

            if hasattr(session_ctx, "__aenter__"):
                async with session_ctx as session:
                    res = await session.execute(query, {"lat": lat, "lon": lon})
                    row = res.fetchone()
            else:
                def _sync_query() -> Any:
                    with session_ctx as session:
                        return session.execute(query, {"lat": lat, "lon": lon}).fetchone()

                row = await asyncio.to_thread(_sync_query)

            if row:
                return {
                    "ward_id": str(row[0]),
                    "ward_name": str(row[1]),
                    "zone_name": str(row[2]) if len(row) > 2 else "PMC Main Zone",
                    "boundary_matched": True,
                    "confidence": 0.99,
                }
        except Exception as err:
            logger.warning(f"[GeoValidator] PostGIS query failed ({err}), dropping back to PMC bounding box match.")
        return None


    def _query_pmc_bounding_box(self, lat: float, lon: float) -> GeoValidationResult:
        """Determines ward boundary match using PMC polygon bounding boxes."""
        for ward in PUNE_PMC_BOUNDARIES:
            min_lat = float(ward["min_lat"])
            max_lat = float(ward["max_lat"])
            min_lon = float(ward["min_lon"])
            max_lon = float(ward["max_lon"])

            if min_lat <= lat <= max_lat and min_lon <= lon <= max_lon:
                return {
                    "ward_id": str(ward["ward_id"]),
                    "ward_name": str(ward["ward_name"]),
                    "zone_name": str(ward["zone_name"]),
                    "boundary_matched": True,
                    "confidence": 0.92,
                }

        # Out-of-bounds PMC boundary fallback
        return self._build_fallback(reason="Coordinates outside PMC jurisdiction")

    def _build_fallback(self, reason: str) -> GeoValidationResult:
        """Fallback payload when spatial match fails."""
        return {
            "ward_id": None,
            "ward_name": "Unknown Ward",
            "zone_name": "Unassigned Zone",
            "boundary_matched": False,
            "confidence": 0.0,
        }
