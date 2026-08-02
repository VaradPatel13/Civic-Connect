"""Phase-1G Audit & Observability Utilities for CivicConnect.

Provides structured trace generation, secret redaction, error classification,
and PII-safe evidence snapshot helpers for AI agent executions.
"""

from __future__ import annotations

import logging
import re
import time
from datetime import UTC, datetime
from typing import Any

from backend.core.pii_masker import mask_pii

logger = logging.getLogger(__name__)

# ── Secret Redaction Patterns ────────────────────────────────────────────────
SECRET_PATTERNS: list[tuple[re.Pattern[str], str]] = [
    (re.compile(r"(?i)bearer\s+[a-z0-9._-]+"), "Bearer [REDACTED_TOKEN]"),
    (re.compile(r"nvapi-[A-Za-z0-9_-]+"), "[REDACTED_NVIDIA_KEY]"),
    (re.compile(r"eyJ[A-Za-z0-9_-]+\.[A-Za-z0-9_-]+\.[A-Za-z0-9_-]+"), "[REDACTED_JWT]"),
    (re.compile(r"(?i)(key|secret|password|token)\s*=\s*['\"][^'\"]+['\"]"), r"\1='[REDACTED]'"),
    (re.compile(r"postgresql(\+asyncpg)?://[^:@]+:[^@]+@"), "postgresql://[REDACTED_CREDENTIALS]@"),
]


def redact_secrets(text: str) -> str:
    """Redacts API keys, JWT tokens, Bearer tokens, and database passwords from text."""
    if not text:
        return ""
    sanitized = str(text)
    for pattern, replacement in SECRET_PATTERNS:
        sanitized = pattern.sub(replacement, sanitized)
    return sanitized


def classify_error(exc: Exception | str) -> tuple[str, str, str]:
    """Classifies exceptions into structured, audit-safe error categories.

    Returns:
        (error_code, error_type, safe_message)
    """
    if isinstance(exc, str):
        msg = redact_secrets(exc)
        exc_type = "StringError"
    else:
        msg = redact_secrets(str(exc))
        exc_type = exc.__class__.__name__

    msg_lower = msg.lower()

    if "timeout" in msg_lower or "timed out" in msg_lower:
        code = "PROVIDER_TIMEOUT"
    elif "429" in msg_lower or "rate limit" in msg_lower or "quota" in msg_lower:
        code = "PROVIDER_RATE_LIMIT"
    elif "http" in msg_lower or "status code" in msg_lower or "500" in msg_lower or "502" in msg_lower or "503" in msg_lower:
        code = "PROVIDER_HTTP_ERROR"
    elif "json" in msg_lower or "malformed" in msg_lower or "decode" in msg_lower or "parse" in msg_lower:
        code = "PROVIDER_MALFORMED_RESPONSE"
    elif "postgis" in msg_lower or "spatial" in msg_lower or "geometry" in msg_lower:
        code = "POSTGIS_QUERY_FAILURE"
    elif "database" in msg_lower or "operationalerror" in msg_lower or "connection" in msg_lower:
        code = "DATABASE_UNAVAILABLE"
    elif "contract" in msg_lower or "prerequisite" in msg_lower or "decision" in msg_lower:
        code = "CONTRACT_VALIDATION_FAILURE"
    elif "graph" in msg_lower or "langgraph" in msg_lower or "pipeline" in msg_lower:
        code = "PIPELINE_GRAPH_FAILURE"
    else:
        code = "UNKNOWN_INTERNAL_ERROR"

    return code, exc_type, msg[:300]


def build_audit_safe_input_snapshot(
    node_name: str,
    raw_payload: dict[str, Any] | None,
    sanitised_text: str | None = None,
) -> dict[str, Any]:
    """Builds a PII-masked, secret-redacted, size-bounded input snapshot for audit records."""
    if not raw_payload:
        return {"node_name": node_name}

    title = str(raw_payload.get("title") or "")
    safe_title, _ = mask_pii(title)

    media_urls = raw_payload.get("media_urls") or []
    if not isinstance(media_urls, list):
        media_urls = []

    # Count attached photos without storing raw bytes/base64
    media_summary = {
        "count": len(media_urls),
        "has_media": len(media_urls) > 0,
    }

    snapshot: dict[str, Any] = {
        "node_name": node_name,
        "category": raw_payload.get("category"),
        "title_sanitized": redact_secrets(safe_title[:100]),
        "media_summary": media_summary,
        "sanitised_text_present": bool(sanitised_text),
    }

    # Include coarse location metadata if present, avoiding duplicate exact coordinates
    if raw_payload.get("address"):
        addr_clean, _ = mask_pii(str(raw_payload["address"]))
        snapshot["address_sanitized"] = redact_secrets(addr_clean[:100])

    return snapshot


def build_audit_safe_output_snapshot(
    node_name: str,
    output_dict: dict[str, Any],
    provider: str = "INTERNAL",
    model: str = "UNKNOWN",
) -> dict[str, Any]:
    """Builds a sanitized, PII-safe output snapshot for audit storage."""
    snapshot: dict[str, Any] = {
        "node_name": node_name,
        "provider": provider,
        "model": model,
        "analysis_status": output_dict.get("analysis_status", "SUCCESS"),
    }

    if node_name == "safety":
        snapshot.update({
            "clean": output_dict.get("clean"),
            "flags": output_dict.get("flags", []),
            "confidence": output_dict.get("confidence"),
            "injection_detected": output_dict.get("injection_detected"),
        })
    elif node_name == "visual_verification":
        signals = output_dict.get("signals", {}) if isinstance(output_dict.get("signals"), dict) else {}
        snapshot.update({
            "supports_report": output_dict.get("supports_report"),
            "evidence_confidence": output_dict.get("evidence_confidence"),
            "risk_flags": output_dict.get("risk_flags", []),
            "signature_valid": signals.get("signature_valid"),
            "screenshot_suspected": signals.get("screenshot_suspected"),
            "photo_of_screen_suspected": signals.get("photo_of_screen_suspected"),
            "synthetic_image_suspected": signals.get("synthetic_image_suspected"),
            "exact_duplicate_found": signals.get("exact_duplicate_found"),
            "perceptual_duplicate_found": signals.get("perceptual_duplicate_found"),
            "exif_present": signals.get("exif_present"),
        })
    elif node_name == "geo_validator":
        snapshot.update({
            "coordinates_valid": output_dict.get("coordinates_valid"),
            "municipality_matched": output_dict.get("municipality_matched"),
            "boundary_matched": output_dict.get("boundary_matched"),
            "near_boundary": output_dict.get("near_boundary"),
            "confidence": output_dict.get("confidence"),
            "ward_id": output_dict.get("ward_id"),
            "ward_name": output_dict.get("ward_name"),
            "zone_name": output_dict.get("zone_name"),
        })
    elif node_name == "issue_intelligence":
        details = output_dict.get("details", {}) if isinstance(output_dict.get("details"), dict) else {}
        snapshot.update({
            "civic_relevance": output_dict.get("civic_relevance"),
            "category": output_dict.get("category"),
            "subcategory": output_dict.get("subcategory"),
            "severity": output_dict.get("severity"),
            "urgency": output_dict.get("urgency"),
            "confidence": output_dict.get("confidence"),
            "tags": output_dict.get("tags", []),
            "analysis_source": details.get("analysis_source", "MODEL" if not output_dict.get("fallback_used") else "DETERMINISTIC_ONLY"),
            "fallback_used": output_dict.get("fallback_used", False),
        })
    elif node_name == "quality_gate":
        snapshot.update({
            "verification_decision": output_dict.get("verification_decision"),
            "policy_version": output_dict.get("policy_version"),
            "reason_codes": output_dict.get("reason_codes", []),
            "policy_score": output_dict.get("policy_score"),
            "trust_score": output_dict.get("trust_score"),
            "requires_manual_review": output_dict.get("requires_manual_review"),
        })
    else:
        # Generic safe dictionary pass-through
        for k, v in output_dict.items():
            if k not in ("raw_payload", "description", "prompt", "media_bytes", "jwt"):
                snapshot[k] = v

    return snapshot


def create_node_trace_metadata(
    node_name: str,
    workflow_run_id: str,
    report_id: str,
    start_mono: float,
    end_mono: float,
    started_at_utc: datetime,
    ended_at_utc: datetime,
    output_dict: dict[str, Any],
    provider: str,
    model: str,
    error: Exception | str | None = None,
) -> dict[str, Any]:
    """Constructs an immutable node execution trace metadata block."""
    duration_ms = max(0, int((end_mono - start_mono) * 1000))
    execution_status = "FAILED" if error else "COMPLETED"
    analysis_status = output_dict.get("analysis_status", "UNAVAILABLE" if error else "SUCCESS")

    trace: dict[str, Any] = {
        "workflow_run_id": workflow_run_id,
        "report_id": report_id,
        "node_name": node_name,
        "execution_status": execution_status,
        "analysis_status": analysis_status,
        "started_at": started_at_utc.isoformat(),
        "completed_at": ended_at_utc.isoformat(),
        "duration_ms": duration_ms,
        "provider": provider,
        "model": model,
        "confidence": output_dict.get("confidence") or output_dict.get("evidence_confidence"),
        "fallback_used": bool(output_dict.get("fallback_used", False)),
        "risk_flags": output_dict.get("risk_flags", []),
    }

    if error:
        err_code, err_type, safe_msg = classify_error(error)
        trace["error_code"] = err_code
        trace["error_type"] = err_type
        trace["error_message"] = safe_msg

    return trace
