"""Phase-1D Geo Verification Component for CivicConnect.

Responsibility:
Validates citizen-submitted GPS report coordinates against municipal jurisdiction
and administrative department service area boundaries.

Core Security & Architectural Principles:
1. Citizen coordinates = UNTRUSTED LOCATION EVIDENCE.
2. Coordinates inside municipality != proof of genuine physical presence.
3. Geo Verification emits STRUCTURED EVIDENCE SIGNALS; it NEVER directly emits
   VERIFIED, REJECTED, or PENDING_MANUAL_REVIEW (Quality Gate retains final decision).
4. Strict Three-State Semantics:
   - TRUE: Confirmed authoritative PostGIS spatial match / valid coordinate.
   - FALSE: Confirmed out-of-bounds / invalid coordinate.
   - NONE (UNKNOWN): Infrastructure / GIS unavailable OR unconfirmed bounding-box fallback.
5. PostGIS Point Ordering: ST_MakePoint(longitude, latitude) under EPSG:4326.
6. MultiPolygon Boundary Distance: Uses ST_Distance(point::geography, ST_Boundary(geom)::geography).
7. SQL Injection Safety: All spatial queries strictly parameterized.
8. Bounding-Box Fallback: Pune regional envelope & PUNE_PMC_BOUNDARIES are development
   approximations; they set analysis_status="PARTIAL", signals["approximate_boundary_match"]=True,
   and boundary_matched=None (they do NOT masquerade as authoritative GIS proof).
9. Confidence Semantics: geo["confidence"] is ANALYSIS CONFIDENCE in the geographic calculation
   itself, NOT citizen/report trust.

Specs: docs/specs/ai-pipeline.md, docs/specs/AGENT.md
"""

from __future__ import annotations

import asyncio
import logging
import math
import time
from typing import Any, TypedDict

from sqlalchemy import text

from backend.agents.state import GeoValidationResult, PipelineSharedState
from backend.core.config import settings

logger = logging.getLogger(__name__)


class PMCBoundaryDict(TypedDict):
    ward_id: str
    ward_name: str
    zone_name: str
    min_lat: float
    max_lat: float
    min_lon: float
    max_lon: float


# Development / Mock Pune Municipal Corporation (PMC) ward bounding box approximations
PUNE_PMC_BOUNDARIES: list[PMCBoundaryDict] = [
    {"ward_id": "WARD_01", "ward_name": "Aundh-Baner", "zone_name": "Zone 1", "min_lat": 18.54, "max_lat": 18.58, "min_lon": 73.78, "max_lon": 73.83},
    {"ward_id": "WARD_02", "ward_name": "Kothrud-Bavdhan", "zone_name": "Zone 1", "min_lat": 18.49, "max_lat": 18.53, "min_lon": 73.79, "max_lon": 73.83},
    {"ward_id": "WARD_03", "ward_name": "Shivajinagar-Ghole Road", "zone_name": "Zone 2", "min_lat": 18.51, "max_lat": 18.54, "min_lon": 73.83, "max_lon": 73.86},
    {"ward_id": "WARD_04", "ward_name": "Kasba-Vishrambaug Wada", "zone_name": "Zone 2", "min_lat": 18.50, "max_lat": 18.52, "min_lon": 73.84, "max_lon": 73.87},
    {"ward_id": "WARD_05", "ward_name": "Hadapsar-Mundhwa", "zone_name": "Zone 3", "min_lat": 18.48, "max_lat": 18.53, "min_lon": 73.90, "max_lon": 73.96},
]


class GeoValidationAgent:
    """Agent performing spatial boundary verification and evidence signal extraction."""

    def __init__(self, db_session_factory: Any | None = None) -> None:
        self.db_session_factory = db_session_factory

    async def process(self, state: PipelineSharedState) -> dict[str, Any]:
        """Executes Phase-1D Geo Verification logic asynchronously."""
        start_time = time.time()
        raw_payload = state.get("raw_payload", {})

        latitude_raw = raw_payload.get("latitude")
        longitude_raw = raw_payload.get("longitude")
        accuracy_raw = raw_payload.get("accuracy_meters") or raw_payload.get("location_accuracy_meters")
        source_raw = raw_payload.get("location_source") or raw_payload.get("capture_source")

        # Parse accuracy and source hints if present
        accuracy_meters: float | None = None
        if accuracy_raw is not None:
            try:
                acc_val = float(accuracy_raw)
                if not math.isnan(acc_val) and not math.isinf(acc_val) and acc_val >= 0.0:
                    accuracy_meters = acc_val
            except (TypeError, ValueError):
                accuracy_meters = None

        location_source: str | None = str(source_raw) if source_raw else None

        # ── 1. Coordinate Presence & Structural Validation ────────────────────
        if latitude_raw is None or longitude_raw is None:
            logger.warning("[GeoValidator] Missing latitude/longitude in report payload.")
            result = self._build_missing_coordinates_result(accuracy_meters, location_source)
            return {"agent_outputs": {"geo_validation": result, "geo": result}}

        try:
            lat = float(latitude_raw)
            lon = float(longitude_raw)
        except (ValueError, TypeError):
            logger.warning(f"[GeoValidator] Non-numeric coordinates: lat={latitude_raw}, lon={longitude_raw}")
            result = self._build_invalid_coordinates_result(accuracy_meters, location_source)
            return {"agent_outputs": {"geo_validation": result, "geo": result}}

        # Structural bounds & NaN / Infinity checks
        if (
            math.isnan(lat)
            or math.isnan(lon)
            or math.isinf(lat)
            or math.isinf(lon)
            or not (-90.0 <= lat <= 90.0)
            or not (-180.0 <= lon <= 180.0)
        ):
            logger.warning(f"[GeoValidator] Out-of-bounds or NaN/Inf coordinates: ({lat}, {lon})")
            result = self._build_invalid_coordinates_result(accuracy_meters, location_source)
            return {"agent_outputs": {"geo_validation": result, "geo": result}}

        # ── 2. Regional Municipal Envelope Check ──────────────────────────────
        # Pune Regional Envelope (18.0 <= lat <= 19.0 and 73.0 <= lon <= 74.5)
        is_in_regional_envelope = 18.0 <= lat <= 19.0 and 73.0 <= lon <= 74.5
        if not is_in_regional_envelope:
            logger.warning(f"[GeoValidator] Coordinates ({lat}, {lon}) outside Pune regional envelope.")
            result = self._build_outside_municipality_result(lat, lon, accuracy_meters, location_source)
            return {"agent_outputs": {"geo_validation": result, "geo": result}}

        # ── 3. Authoritative PostGIS Spatial Query Attempt ──────────────────────
        if self.db_session_factory is not None:
            spatial_match = await self._query_postgis_ward(lat, lon, accuracy_meters, location_source)
            if spatial_match is not None:
                execution_ms = (time.time() - start_time) * 1000.0
                logger.info(
                    f"[GeoValidator] PostGIS query completed in {execution_ms:.2f}ms. "
                    f"Status: {spatial_match['analysis_status']} Matched: {spatial_match['boundary_matched']}"
                )
                return {"agent_outputs": {"geo_validation": spatial_match, "geo": spatial_match}}

        # ── 4. Development Bounding Box Fallback (No DB session or DB query failure)
        result = self._query_pmc_bounding_box(lat, lon, accuracy_meters, location_source)
        execution_ms = (time.time() - start_time) * 1000.0
        logger.info(f"[GeoValidator] Geo-validation fallback completed in {execution_ms:.2f}ms. Status: {result['analysis_status']}")

        return {"agent_outputs": {"geo_validation": result, "geo": result}}

    async def _query_postgis_ward(
        self, lat: float, lon: float, accuracy_meters: float | None, location_source: str | None
    ) -> GeoValidationResult | None:
        """Queries PostGIS database using ST_Covers and ST_Distance geography calculations.

        IMPORTANT POSTGIS POINT CONVENTION:
          ST_MakePoint(:lon, :lat)  -->  Longitude FIRST, Latitude SECOND.
        """
        factory = self.db_session_factory
        if factory is None:
            return None

        uncertainty_threshold = float(getattr(settings, "geo_boundary_uncertainty_meters", 30.0))

        try:
            # Query PostGIS with parameterized inputs (SQL injection safe)
            # Supports both Polygon and MultiPolygon geometry boundaries
            query = text("""
                SELECT code, name, category,
                       ST_Covers(jurisdiction_geometry, ST_SetSRID(ST_MakePoint(:lon, :lat), 4326)) AS covered,
                       ST_Distance(
                           ST_SetSRID(ST_MakePoint(:lon, :lat), 4326)::geography,
                           ST_Boundary(jurisdiction_geometry)::geography
                       ) AS dist_meters
                FROM departments
                WHERE jurisdiction_geometry IS NOT NULL
                ORDER BY covered DESC, dist_meters ASC
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
                ward_code, ward_name, category, covered, dist_m = row[0], row[1], row[2], bool(row[3]), float(row[4]) if row[4] is not None else 0.0

                near_bnd = dist_m <= uncertainty_threshold
                risk_flags: list[str] = []
                if near_bnd:
                    risk_flags.append("near_ward_boundary")

                # geo.confidence measures ANALYSIS CONFIDENCE in the geographic calculation
                analysis_confidence = 0.95 if covered and not near_bnd else (0.80 if covered else 0.95)

                return {
                    "analysis_status": "SUCCESS",
                    "coordinates_valid": True,
                    "municipality_matched": covered,
                    "boundary_matched": covered,
                    "ward_id": str(ward_code),
                    "ward_name": str(ward_name),
                    "zone_name": str(category) if category else "PMC Main Zone",
                    "near_boundary": near_bnd,
                    "confidence": analysis_confidence,
                    "signals": {
                        "coordinates_valid": True,
                        "municipality_matched": covered,
                        "boundary_matched": covered,
                        "near_boundary": near_bnd,
                        "location_accuracy_meters": accuracy_meters,
                        "location_source": location_source,
                    },
                    "risk_flags": risk_flags,
                    "details": {
                        "boundary_distance_meters": round(dist_m, 2),
                        "boundary_uncertainty_threshold_meters": uncertainty_threshold,
                        "srid": 4326,
                        "point_wkt": f"POINT({lon} {lat})",
                        "boundary_source": "postgis_department_geometry",
                        "jurisdiction_type": "department_service_area",
                    },
                }

        except Exception as err:
            logger.warning(f"[GeoValidator] PostGIS query failed ({err}). Returning UNAVAILABLE failure payload.")
            # System / Infrastructure failure MUST return UNAVAILABLE with None signals (never REJECTED)
            return self._build_unavailable_result(accuracy_meters, location_source, str(err))

        return None

    def _query_pmc_bounding_box(
        self, lat: float, lon: float, accuracy_meters: float | None, location_source: str | None
    ) -> GeoValidationResult:
        """Determines ward match using PMC development bounding boxes (approximate fallback).

        CRITICAL SECURITY REQUIREMENT:
        Development bounding box matches MUST NOT masquerade as authoritative GIS proof.
        Returns analysis_status="PARTIAL", boundary_matched=None, and municipality_matched=None.
        """
        uncertainty_threshold = float(getattr(settings, "geo_boundary_uncertainty_meters", 30.0))

        for ward in PUNE_PMC_BOUNDARIES:
            min_lat = float(ward["min_lat"])
            max_lat = float(ward["max_lat"])
            min_lon = float(ward["min_lon"])
            max_lon = float(ward["max_lon"])

            if min_lat <= lat <= max_lat and min_lon <= lon <= max_lon:
                near_bnd = (
                    abs(lat - min_lat) < 0.0003
                    or abs(lat - max_lat) < 0.0003
                    or abs(lon - min_lon) < 0.0003
                    or abs(lon - max_lon) < 0.0003
                )
                risk_flags = ["approximate_boundary_match", "unconfirmed_authoritative_boundary"]
                if near_bnd:
                    risk_flags.append("near_ward_boundary")

                return {
                    "analysis_status": "PARTIAL",
                    "coordinates_valid": True,
                    "municipality_matched": None,  # Authoritative polygon match unconfirmed
                    "boundary_matched": None,      # Authoritative ward polygon match unconfirmed
                    "ward_id": str(ward["ward_id"]),
                    "ward_name": str(ward["ward_name"]),
                    "zone_name": str(ward["zone_name"]),
                    "near_boundary": near_bnd,
                    "confidence": 0.50,  # Partial analysis confidence due to dev bbox
                    "signals": {
                        "coordinates_valid": True,
                        "municipality_matched": None,
                        "boundary_matched": None,
                        "regional_envelope_matched": True,
                        "approximate_boundary_match": True,
                        "near_boundary": near_bnd,
                        "location_accuracy_meters": accuracy_meters,
                        "location_source": location_source,
                    },
                    "risk_flags": risk_flags,
                    "details": {
                        "boundary_source": "development_bbox",
                        "boundary_uncertainty_threshold_meters": uncertainty_threshold,
                        "note": "Authoritative PostGIS spatial geometry lookup unavailable; matched development bbox",
                    },
                }

        # Inside Pune regional envelope, but outside specific development bounding boxes
        return {
            "analysis_status": "PARTIAL",
            "coordinates_valid": True,
            "municipality_matched": None,
            "boundary_matched": None,
            "ward_id": None,
            "ward_name": "Unknown Ward",
            "zone_name": "Unassigned Zone",
            "near_boundary": False,
            "confidence": 0.30,
            "signals": {
                "coordinates_valid": True,
                "municipality_matched": None,
                "boundary_matched": None,
                "regional_envelope_matched": True,
                "approximate_boundary_match": False,
                "near_boundary": False,
                "location_accuracy_meters": accuracy_meters,
                "location_source": location_source,
            },
            "risk_flags": ["unassigned_ward_location", "unconfirmed_authoritative_boundary"],
            "details": {
                "boundary_source": "regional_envelope",
                "note": "Inside Pune regional envelope, but outside development ward bounding boxes",
            },
        }

    def _build_missing_coordinates_result(
        self, accuracy_meters: float | None, location_source: str | None
    ) -> GeoValidationResult:
        """Payload when coordinates are absent."""
        return {
            "analysis_status": "PARTIAL",
            "coordinates_valid": None,
            "municipality_matched": None,
            "boundary_matched": None,
            "ward_id": None,
            "ward_name": "Unknown Ward",
            "zone_name": "Unassigned Zone",
            "near_boundary": None,
            "confidence": 0.0,
            "signals": {
                "coordinates_valid": None,
                "municipality_matched": None,
                "boundary_matched": None,
                "near_boundary": None,
                "location_accuracy_meters": accuracy_meters,
                "location_source": location_source,
            },
            "risk_flags": ["missing_gps_coordinates"],
            "details": {"reason": "Missing GPS coordinates"},
        }

    def _build_invalid_coordinates_result(
        self, accuracy_meters: float | None, location_source: str | None
    ) -> GeoValidationResult:
        """Payload when coordinates are non-numeric, NaN, Infinity, or out of lat/lon range."""
        return {
            "analysis_status": "SUCCESS",
            "coordinates_valid": False,
            "municipality_matched": False,
            "boundary_matched": False,
            "ward_id": None,
            "ward_name": "Unknown Ward",
            "zone_name": "Unassigned Zone",
            "near_boundary": False,
            "confidence": 1.0,  # Highly confident in the invalidity determination
            "signals": {
                "coordinates_valid": False,
                "municipality_matched": False,
                "boundary_matched": False,
                "near_boundary": False,
                "location_accuracy_meters": accuracy_meters,
                "location_source": location_source,
            },
            "risk_flags": ["structurally_invalid_coordinates"],
            "details": {"reason": "Structurally invalid coordinates (NaN, Infinity, or out of range)"},
        }

    def _build_outside_municipality_result(
        self, lat: float, lon: float, accuracy_meters: float | None, location_source: str | None
    ) -> GeoValidationResult:
        """Payload when coordinates are confirmed outside municipal regional boundary."""
        return {
            "analysis_status": "SUCCESS",
            "coordinates_valid": True,
            "municipality_matched": False,
            "boundary_matched": False,
            "ward_id": None,
            "ward_name": "Unknown Ward",
            "zone_name": "Unassigned Zone",
            "near_boundary": False,
            "confidence": 0.95,  # High analysis confidence in negative determination
            "signals": {
                "coordinates_valid": True,
                "municipality_matched": False,
                "boundary_matched": False,
                "near_boundary": False,
                "location_accuracy_meters": accuracy_meters,
                "location_source": location_source,
            },
            "risk_flags": ["outside_supported_municipality"],
            "details": {
                "latitude": lat,
                "longitude": lon,
                "reason": "Coordinates fall outside Pune metropolitan regional boundary",
            },
        }

    def _build_unavailable_result(
        self, accuracy_meters: float | None, location_source: str | None, error_msg: str
    ) -> GeoValidationResult:
        """Three-state failure payload when GIS / PostGIS database is unavailable.

        MUST NOT reject citizen; sets three-state signals to None (UNKNOWN).
        """
        return {
            "analysis_status": "UNAVAILABLE",
            "coordinates_valid": True,
            "municipality_matched": None,
            "boundary_matched": None,
            "ward_id": None,
            "ward_name": "Unknown Ward",
            "zone_name": "Unassigned Zone",
            "near_boundary": None,
            "confidence": 0.0,
            "signals": {
                "coordinates_valid": True,
                "municipality_matched": None,
                "boundary_matched": None,
                "near_boundary": None,
                "location_accuracy_meters": accuracy_meters,
                "location_source": location_source,
            },
            "risk_flags": ["geo_database_unavailable"],
            "details": {
                "error": error_msg,
                "reason": "GIS / PostGIS database service unavailable or timed out",
            },
        }
