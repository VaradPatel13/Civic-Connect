"""Phase-1F Trust / Quality Gate Policy Engine for CivicConnect.

The Quality Gate is the ONLY Phase-1 component authorized to produce the final
verification_decision:
  - VERIFIED
  - REJECTED
  - PENDING_MANUAL_REVIEW

Architectural Invariants:
1. Deterministic & Explainable Policy Ladder: Pure functional logic, NO LLMs, NO network/DB calls.
2. Failure != Rejection: Infrastructure/provider failures yield PENDING_MANUAL_REVIEW, NEVER REJECTED.
3. No Confidence Probability Averaging: Confidence scores measure different domain uncertainties
   and are NOT multiplied or averaged together as probabilities.
4. Explanations & Reason Codes: Every decision returns machine-readable reason codes and concise human-readable explanations.
5. Strict Contract Compatibility: Emits policy_version, reason_codes, evidence_summary, policy_score,
   while remaining 100% backward compatible with decision_reasons and trust_score.
"""

from __future__ import annotations

import logging
import math
from typing import Any, Final

DECISION_VERIFIED: Final[str] = "VERIFIED"
DECISION_REJECTED: Final[str] = "REJECTED"
DECISION_PENDING_MANUAL_REVIEW: Final[str] = "PENDING_MANUAL_REVIEW"

logger = logging.getLogger(__name__)

# ── Policy Engine Constants ──────────────────────────────────────────────────
QUALITY_GATE_POLICY_VERSION: Final[str] = "1F-2026.1"

# Named Policy Thresholds
MIN_ISSUE_MODEL_CONFIDENCE: Final[float] = 0.60
MIN_VISUAL_EVIDENCE_CONFIDENCE: Final[float] = 0.50
MAX_PERMITTED_VISUAL_RISK_FLAGS: Final[int] = 1
NON_CIVIC_REJECT_CONFIDENCE_THRESHOLD: Final[float] = 0.70
OUTSIDE_JURISDICTION_REJECT_CONFIDENCE_THRESHOLD: Final[float] = 0.80

# Structured Reason Codes
REASON_QG_VERIFICATION_POLICY_SATISFIED: Final[str] = "QG_VERIFICATION_POLICY_SATISFIED"

# Prerequisite & Contract Failures
REASON_QG_MISSING_COMPONENT: Final[str] = "QG_MISSING_COMPONENT"
REASON_QG_MALFORMED_COMPONENT: Final[str] = "QG_MALFORMED_COMPONENT"

# Infrastructure & Service Failures
REASON_QG_SAFETY_UNAVAILABLE: Final[str] = "QG_SAFETY_UNAVAILABLE"
REASON_QG_VISUAL_UNAVAILABLE: Final[str] = "QG_VISUAL_UNAVAILABLE"
REASON_QG_GEO_UNAVAILABLE: Final[str] = "QG_GEO_UNAVAILABLE"
REASON_QG_ISSUE_UNAVAILABLE: Final[str] = "QG_ISSUE_UNAVAILABLE"

# Explicit Policy Rejections
REASON_QG_SAFETY_BLOCK: Final[str] = "QG_SAFETY_BLOCK"
REASON_QG_INVALID_COORDINATES: Final[str] = "QG_INVALID_COORDINATES"
REASON_QG_OUTSIDE_JURISDICTION: Final[str] = "QG_OUTSIDE_JURISDICTION"
REASON_QG_NON_CIVIC: Final[str] = "QG_NON_CIVIC"

# Material Contradiction & Review Conditions
REASON_QG_PROMPT_INJECTION_DETECTED: Final[str] = "QG_PROMPT_INJECTION_DETECTED"
REASON_QG_SAFETY_REVIEW: Final[str] = "QG_SAFETY_REVIEW"
REASON_QG_INVALID_SIGNATURE: Final[str] = "QG_INVALID_SIGNATURE"
REASON_QG_VISUAL_CONTRADICTION: Final[str] = "QG_VISUAL_CONTRADICTION"
REASON_QG_ISSUE_AMBIGUOUS: Final[str] = "QG_ISSUE_AMBIGUOUS"
REASON_QG_HEURISTIC_ONLY_ISSUE: Final[str] = "QG_HEURISTIC_ONLY_ISSUE"
REASON_QG_ISSUE_LOW_CONFIDENCE: Final[str] = "QG_ISSUE_LOW_CONFIDENCE"
REASON_QG_VISUAL_LOW_CONFIDENCE: Final[str] = "QG_VISUAL_LOW_CONFIDENCE"
REASON_QG_VISUAL_RISK: Final[str] = "QG_VISUAL_RISK"
REASON_QG_GEO_UNCONFIRMED: Final[str] = "QG_GEO_UNCONFIRMED"
REASON_QG_MINIMUM_EVIDENCE_NOT_MET: Final[str] = "QG_MINIMUM_EVIDENCE_NOT_MET"

REQUIRED_COMPONENTS: Final[list[str]] = [
    "safety",
    "visual_verification",
    "geo_validation",
    "issue_intelligence",
]


def _build_evidence_summary(
    safety: dict[str, Any],
    visual: dict[str, Any],
    geo: dict[str, Any],
    issue: dict[str, Any],
) -> dict[str, Any]:
    """Builds a compact, sanitized summary of agent evidence for audit/logging."""
    details = issue.get("details", {})
    analysis_source = details.get("analysis_source") if isinstance(details, dict) else "NONE"
    if not analysis_source:
        analysis_source = "DETERMINISTIC_ONLY" if issue.get("fallback_used") else "MODEL"

    geo_signals = geo.get("signals", {}) if isinstance(geo.get("signals"), dict) else {}
    approx_match = bool(geo_signals.get("approximate_boundary_match", False)) or geo.get("regional_envelope_matched") is True

    return {
        "safety": {
            "status": safety.get("analysis_status", "UNKNOWN"),
            "clean": safety.get("clean"),
            "flags_count": len(safety.get("flags", [])),
            "injection_detected": bool(safety.get("injection_detected", False)),
        },
        "visual": {
            "status": visual.get("analysis_status", "UNKNOWN"),
            "supports_report": visual.get("supports_report"),
            "evidence_confidence": visual.get("evidence_confidence"),
            "risk_flags_count": len(visual.get("risk_flags", [])),
            "no_image": bool(visual.get("signals", {}).get("no_image_attached", False)),
            "signature_valid": visual.get("signals", {}).get("signature_valid"),
        },
        "geo": {
            "status": geo.get("analysis_status", "UNKNOWN"),
            "coordinates_valid": geo.get("coordinates_valid"),
            "municipality_matched": geo.get("municipality_matched"),
            "boundary_matched": geo.get("boundary_matched"),
            "near_boundary": geo.get("near_boundary"),
            "approximate_boundary_match": approx_match,
        },
        "issue": {
            "status": issue.get("analysis_status", "UNKNOWN"),
            "civic_relevance": issue.get("civic_relevance"),
            "category": issue.get("category"),
            "confidence": issue.get("confidence"),
            "analysis_source": analysis_source,
        },
    }


def _calculate_policy_score(
    decision: str,
    safety: dict[str, Any],
    visual: dict[str, Any],
    geo: dict[str, Any],
    issue: dict[str, Any],
) -> int:
    """Calculates a diagnostic heuristic policy score (0-100).

    NOTE: This is a diagnostic policy metric, NOT a probability score.
    """
    if decision == DECISION_REJECTED:
        return 0

    score = 50

    # Safety contribution
    if safety.get("clean") is True:
        score += 15

    # Issue contribution
    details = issue.get("details", {})
    source = details.get("analysis_source") if isinstance(details, dict) else "MODEL"
    conf = issue.get("confidence")
    if isinstance(conf, (int, float)) and conf >= 0.70 and source in ("MODEL", "MODEL_PLUS_RULES"):
        score += 15
    elif source == "DETERMINISTIC_ONLY" or issue.get("fallback_used"):
        score -= 15

    # Geo contribution
    geo_signals = geo.get("signals", {}) if isinstance(geo.get("signals"), dict) else {}
    approx_match = bool(geo_signals.get("approximate_boundary_match", False)) or geo.get("regional_envelope_matched") is True
    if geo.get("coordinates_valid") is True and (
        geo.get("municipality_matched") is True or geo.get("boundary_matched") is True or approx_match
    ):
        score += 10

    if geo.get("near_boundary") is True:
        score -= 5

    # Visual contribution
    v_conf = visual.get("evidence_confidence")
    if visual.get("supports_report") is True:
        score += 10
    elif visual.get("supports_report") is False:
        score -= 20

    risk_flags = visual.get("risk_flags", [])
    if isinstance(risk_flags, list) and len(risk_flags) > 0:
        score -= min(len(risk_flags) * 10, 20)

    return max(0, min(100, score))


def evaluate_quality_gate(
    agent_outputs: dict[str, Any] | None,
    report_id: str = "unknown",
) -> dict[str, Any]:
    """Pure functional Quality Gate evaluation engine.

    Evaluates structured evidence outputs across all 4 branches against explicit policy.
    Returns QualityGateResult contract dictionary.
    """
    reason_codes: list[str] = []
    reasons: list[str] = []

    # ── STEP 1: Contract & Prerequisite Validation ───────────────────────────
    if not isinstance(agent_outputs, dict):
        reason_codes.append(REASON_QG_MALFORMED_COMPONENT)
        reasons.append("Agent outputs payload is malformed or missing")
        return {
            "verification_decision": DECISION_PENDING_MANUAL_REVIEW,
            "policy_version": QUALITY_GATE_POLICY_VERSION,
            "reason_codes": reason_codes,
            "reasons": reasons,
            "decision_reasons": reasons,
            "evidence_summary": {},
            "policy_score": 0,
            "trust_score": 0.0,
            "requires_manual_review": True,
        }

    missing_components: list[str] = []
    malformed_components: list[str] = []
    components: dict[str, dict[str, Any]] = {}

    for comp in REQUIRED_COMPONENTS:
        raw_val = agent_outputs.get(comp)
        if raw_val is None:
            missing_components.append(comp)
        elif not isinstance(raw_val, dict):
            malformed_components.append(comp)
        else:
            components[comp] = raw_val

    if missing_components:
        reason_codes.append(REASON_QG_MISSING_COMPONENT)
        for comp in missing_components:
            reasons.append(f"Required verification branch missing: '{comp}'")

    if malformed_components:
        reason_codes.append(REASON_QG_MALFORMED_COMPONENT)
        for comp in malformed_components:
            reasons.append(f"Verification branch output malformed: '{comp}'")

    if missing_components or malformed_components:
        logger.warning(f"[QualityGate] report={report_id} → PENDING_MANUAL_REVIEW | Missing={missing_components} Malformed={malformed_components}")
        return {
            "verification_decision": DECISION_PENDING_MANUAL_REVIEW,
            "policy_version": QUALITY_GATE_POLICY_VERSION,
            "reason_codes": reason_codes,
            "reasons": reasons,
            "decision_reasons": reasons,
            "evidence_summary": {},
            "policy_score": 0,
            "trust_score": 0.0,
            "requires_manual_review": True,
        }

    safety = components["safety"]
    visual = components["visual_verification"]
    geo = components["geo_validation"]
    issue = components["issue_intelligence"]

    evidence_summary = _build_evidence_summary(safety, visual, geo, issue)

    # Extract Evidence Fields Safely (Hardened against NaN / Infinity / Invalid types)
    safety_status = safety.get("analysis_status")
    is_safe = safety.get("clean")
    safety_flags = safety.get("flags", []) if isinstance(safety.get("flags"), list) else []

    visual_status = visual.get("analysis_status")
    visual_supports = visual.get("supports_report")
    visual_conf_raw = visual.get("evidence_confidence")
    visual_conf: float = (
        visual_conf_raw
        if isinstance(visual_conf_raw, (int, float)) and not math.isnan(visual_conf_raw) and not math.isinf(visual_conf_raw)
        else -1.0
    )
    visual_signals = visual.get("signals", {}) if isinstance(visual.get("signals"), dict) else {}
    visual_risk_flags = visual.get("risk_flags", []) if isinstance(visual.get("risk_flags"), list) else []

    geo_status = geo.get("analysis_status")
    coords_valid = geo.get("coordinates_valid")
    muni_matched = geo.get("municipality_matched")
    boundary_matched = geo.get("boundary_matched")
    near_boundary = geo.get("near_boundary")
    geo_conf_raw = geo.get("confidence")
    geo_conf: float = (
        geo_conf_raw
        if isinstance(geo_conf_raw, (int, float)) and not math.isnan(geo_conf_raw) and not math.isinf(geo_conf_raw)
        else 0.0
    )
    geo_signals = geo.get("signals", {}) if isinstance(geo.get("signals"), dict) else {}
    approx_match = bool(geo_signals.get("approximate_boundary_match", False)) or geo.get("regional_envelope_matched") is True

    issue_status = issue.get("analysis_status")
    civic_rel = issue.get("civic_relevance")
    issue_conf_raw = issue.get("confidence")
    issue_conf: float = (
        issue_conf_raw
        if isinstance(issue_conf_raw, (int, float)) and not math.isnan(issue_conf_raw) and not math.isinf(issue_conf_raw)
        else -1.0
    )
    issue_details = issue.get("details", {}) if isinstance(issue.get("details"), dict) else {}
    analysis_source = issue_details.get("analysis_source", "DETERMINISTIC_ONLY" if issue.get("fallback_used") else "MODEL")
    ambiguous_issue = bool(issue.get("ambiguous_issue", False))
    insufficient_info = bool(issue.get("insufficient_information", False))

    # ── STEP 2: Service Infrastructure Availability Checks (Fail-Soft to Review) ─
    if safety_status == "UNAVAILABLE" or is_safe is None:
        reason_codes.append(REASON_QG_SAFETY_UNAVAILABLE)
        reasons.append(f"Safety verification service unavailable or incomplete (flags: {safety_flags})")

    if issue_status == "UNAVAILABLE":
        reason_codes.append(REASON_QG_ISSUE_UNAVAILABLE)
        reasons.append("Issue Intelligence service unavailable")

    if geo_status == "UNAVAILABLE":
        reason_codes.append(REASON_QG_GEO_UNAVAILABLE)
        reasons.append("Geo Validation service unavailable")

    no_image_attached = bool(visual_signals.get("no_image_attached", False))
    if visual_status == "UNAVAILABLE" and not no_image_attached:
        reason_codes.append(REASON_QG_VISUAL_UNAVAILABLE)
        reasons.append("Visual Verification service unavailable")

    if reason_codes:
        logger.warning(f"[QualityGate] report={report_id} → PENDING_MANUAL_REVIEW | Infrastructure unavailable: {reason_codes}")
        score = _calculate_policy_score(DECISION_PENDING_MANUAL_REVIEW, safety, visual, geo, issue)
        return {
            "verification_decision": DECISION_PENDING_MANUAL_REVIEW,
            "policy_version": QUALITY_GATE_POLICY_VERSION,
            "reason_codes": reason_codes,
            "reasons": reasons,
            "decision_reasons": reasons,
            "evidence_summary": evidence_summary,
            "policy_score": score,
            "trust_score": round(score / 100.0, 3),
            "requires_manual_review": True,
        }

    # ── STEP 3: Explicit Policy Rejections (Explicit High-Confidence Violations) ─
    # 3A. Confirmed Unsafe Content (Blocking Abuse / Malicious Code Attacks)
    if is_safe is False:
        safety_signals = safety.get("signals", {}) if isinstance(safety.get("signals"), dict) else {}
        abuse_detected = bool(safety_signals.get("abuse", {}).get("detected", False)) or "abuse" in safety_flags
        spam_detected = bool(safety_signals.get("spam", {}).get("detected", False)) or "spam" in safety_flags
        inj_detected = bool(safety.get("injection_detected", False)) or "prompt_injection" in safety_flags
        det_signals = safety_signals.get("deterministic_signals", []) if isinstance(safety_signals.get("deterministic_signals"), list) else []

        code_attack_patterns = {"<script", "union select", "drop table", "eval(", "exec("}
        has_code_attack = any(pat in det_signals for pat in code_attack_patterns)

        is_blocking = abuse_detected or (spam_detected and "empty_input" in det_signals) or has_code_attack

        if is_blocking:
            reason_codes.append(REASON_QG_SAFETY_BLOCK)
            reasons.append(f"Report violates safety policy with severe blocking violation: {safety_flags}")
            logger.warning(f"[QualityGate] report={report_id} → REJECTED | Safety flags={safety_flags}")
            return {
                "verification_decision": DECISION_REJECTED,
                "policy_version": QUALITY_GATE_POLICY_VERSION,
                "reason_codes": reason_codes,
                "reasons": reasons,
                "decision_reasons": reasons,
                "evidence_summary": evidence_summary,
                "policy_score": 0,
                "trust_score": 0.0,
                "requires_manual_review": False,
            }

    # 3B. Structurally Invalid Coordinates
    if coords_valid is False:
        reason_codes.append(REASON_QG_INVALID_COORDINATES)
        reasons.append("Report contains structurally invalid GPS coordinates")
        logger.warning(f"[QualityGate] report={report_id} → REJECTED | Invalid coordinates")
        return {
            "verification_decision": DECISION_REJECTED,
            "policy_version": QUALITY_GATE_POLICY_VERSION,
            "reason_codes": reason_codes,
            "reasons": reasons,
            "decision_reasons": reasons,
            "evidence_summary": evidence_summary,
            "policy_score": 0,
            "trust_score": 0.0,
            "requires_manual_review": False,
        }

    # 3C. Confirmed Outside Supported Municipal Jurisdiction (Authoritative PostGIS Win)
    if muni_matched is False and geo_conf >= OUTSIDE_JURISDICTION_REJECT_CONFIDENCE_THRESHOLD:
        reason_codes.append(REASON_QG_OUTSIDE_JURISDICTION)
        reasons.append("Report location is outside Pune Municipal Corporation jurisdiction")
        logger.warning(f"[QualityGate] report={report_id} → REJECTED | Outside PMC jurisdiction")
        return {
            "verification_decision": DECISION_REJECTED,
            "policy_version": QUALITY_GATE_POLICY_VERSION,
            "reason_codes": reason_codes,
            "reasons": reasons,
            "decision_reasons": reasons,
            "evidence_summary": evidence_summary,
            "policy_score": 0,
            "trust_score": 0.0,
            "requires_manual_review": False,
        }

    # 3D. Confirmed Non-Civic Private Issue (High Model Confidence)
    if (
        civic_rel is False
        and analysis_source in ("MODEL", "MODEL_PLUS_RULES")
        and issue_conf >= NON_CIVIC_REJECT_CONFIDENCE_THRESHOLD
    ):
        reason_codes.append(REASON_QG_NON_CIVIC)
        reasons.append("Report describes a non-civic/private issue outside PMC mandate")
        logger.warning(f"[QualityGate] report={report_id} → REJECTED | Non-civic issue (conf={issue_conf:.2f})")
        return {
            "verification_decision": DECISION_REJECTED,
            "policy_version": QUALITY_GATE_POLICY_VERSION,
            "reason_codes": reason_codes,
            "reasons": reasons,
            "decision_reasons": reasons,
            "evidence_summary": evidence_summary,
            "policy_score": 0,
            "trust_score": 0.0,
            "requires_manual_review": False,
        }

    # ── STEP 4: Material Contradiction & Uncertainty Checks (Manual Review) ──
    # 4A. Non-blocking Safety / Prompt Injection Detected / Profanity
    if is_safe is False:
        safety_signals = safety.get("signals", {}) if isinstance(safety.get("signals"), dict) else {}
        inj_detected = bool(safety.get("injection_detected", False)) or "prompt_injection" in safety_flags
        if inj_detected:
            reason_codes.append(REASON_QG_PROMPT_INJECTION_DETECTED)
            reasons.append("Prompt injection attack detected — routed to manual review")
        else:
            reason_codes.append(REASON_QG_SAFETY_REVIEW)
            reasons.append(f"Safety review required for content flags: {safety_flags}")

    # 4B. Cryptographic Signature Validation Failure
    if visual_signals.get("signature_valid") is False:
        reason_codes.append(REASON_QG_INVALID_SIGNATURE)
        reasons.append("HMAC cryptographic media signature validation failed")

    # 4C. Strong Text-Image Contradiction
    if visual_supports is False and visual_conf >= MIN_VISUAL_EVIDENCE_CONFIDENCE:
        reason_codes.append(REASON_QG_VISUAL_CONTRADICTION)
        reasons.append("Visual evidence contradicts reported civic issue description")

    # 4D. Ambiguous or Insufficient Information in Issue Description
    if ambiguous_issue or insufficient_info:
        reason_codes.append(REASON_QG_ISSUE_AMBIGUOUS)
        reasons.append("Issue description is ambiguous or lacks sufficient information")

    # 4E. Heuristic / Deterministic-Only Issue Classification
    if analysis_source == "DETERMINISTIC_ONLY" or issue.get("fallback_used") is True:
        reason_codes.append(REASON_QG_HEURISTIC_ONLY_ISSUE)
        reasons.append("Issue classification relies solely on deterministic heuristic fallback")

    # 4F. Low Issue Intelligence Confidence
    if issue_conf < MIN_ISSUE_MODEL_CONFIDENCE:
        reason_codes.append(REASON_QG_ISSUE_LOW_CONFIDENCE)
        reasons.append(
            "Issue Intelligence confidence unknown"
            if issue_conf_raw is None
            else f"Low classification confidence: {issue_conf:.2f}"
        )

    # 4G. Low Visual Evidence Confidence (When Image Exists)
    if not no_image_attached and (visual_supports is None or visual_conf < MIN_VISUAL_EVIDENCE_CONFIDENCE):
        reason_codes.append(REASON_QG_VISUAL_LOW_CONFIDENCE)
        reasons.append(
            "Visual evidence confidence unknown"
            if visual_conf_raw is None
            else f"Low visual evidence confidence: {visual_conf:.2f}"
        )

    # 4H. Visual Risk Flags & Suspicion Signals
    has_risk_signals = (
        len(visual_risk_flags) >= 2
        or visual_signals.get("screenshot_suspected") is True
        or visual_signals.get("photo_of_screen_suspected") is True
        or visual_signals.get("synthetic_image_suspected") is True
        or visual_signals.get("manipulation_suspected") is True
        or visual_signals.get("exact_duplicate_found") is True
        or visual_signals.get("perceptual_duplicate_found") is True
    )
    if has_risk_signals:
        reason_codes.append(REASON_QG_VISUAL_RISK)
        reasons.append(f"Visual risk or duplicate signals detected: {visual_risk_flags or visual_signals}")

    # 4I. Geo Boundary Uncertainty or Unconfirmed Boundary
    is_geo_unconfirmed = (
        near_boundary is True
        or (boundary_matched is False and muni_matched is not True)
        or (boundary_matched is None and muni_matched is not True and not approx_match)
    )
    if is_geo_unconfirmed:
        reason_codes.append(REASON_QG_GEO_UNCONFIRMED)
        reasons.append(
            "Report location is near ward boundary"
            if near_boundary is True
            else "Geo boundary not confirmed by authoritative GIS"
        )

    if reason_codes:
        logger.warning(f"[QualityGate] report={report_id} → PENDING_MANUAL_REVIEW | Codes={reason_codes}")
        score = _calculate_policy_score(DECISION_PENDING_MANUAL_REVIEW, safety, visual, geo, issue)
        return {
            "verification_decision": DECISION_PENDING_MANUAL_REVIEW,
            "policy_version": QUALITY_GATE_POLICY_VERSION,
            "reason_codes": reason_codes,
            "reasons": reasons,
            "decision_reasons": reasons,
            "evidence_summary": evidence_summary,
            "policy_score": score,
            "trust_score": round(score / 100.0, 3),
            "requires_manual_review": True,
        }

    # ── STEP 5: Verification Policy Satisfaction (VERIFIED) ──────────────────
    # Check absolute minimum requirements for automated verification:
    is_verified = (
        is_safe is True
        and civic_rel is True
        and analysis_source in ("MODEL", "MODEL_PLUS_RULES")
        and issue_conf >= MIN_ISSUE_MODEL_CONFIDENCE
        and coords_valid is True
        and (muni_matched is True or (muni_matched is not False and approx_match))
        and (no_image_attached or (visual_supports is True and visual_conf >= MIN_VISUAL_EVIDENCE_CONFIDENCE))
    )

    if is_verified:
        reason_codes.append(REASON_QG_VERIFICATION_POLICY_SATISFIED)
        reasons.append("All verification signals pass policy thresholds")
        score = _calculate_policy_score(DECISION_VERIFIED, safety, visual, geo, issue)
        trust_score = round(score / 100.0, 3)
        logger.info(f"[QualityGate] report={report_id} → VERIFIED | policy_score={score} trust_score={trust_score}")
        return {
            "verification_decision": DECISION_VERIFIED,
            "policy_version": QUALITY_GATE_POLICY_VERSION,
            "reason_codes": reason_codes,
            "reasons": reasons,
            "decision_reasons": reasons,
            "evidence_summary": evidence_summary,
            "policy_score": score,
            "trust_score": trust_score,
            "requires_manual_review": False,
        }

    # Default fallback
    reason_codes.append(REASON_QG_MINIMUM_EVIDENCE_NOT_MET)
    reasons.append("Minimum evidence requirements for automated verification were not met")
    score = _calculate_policy_score(DECISION_PENDING_MANUAL_REVIEW, safety, visual, geo, issue)
    return {
        "verification_decision": DECISION_PENDING_MANUAL_REVIEW,
        "policy_version": QUALITY_GATE_POLICY_VERSION,
        "reason_codes": reason_codes,
        "reasons": reasons,
        "decision_reasons": reasons,
        "evidence_summary": evidence_summary,
        "policy_score": score,
        "trust_score": round(score / 100.0, 3),
        "requires_manual_review": True,
    }

    if is_verified:
        reason_codes.append(REASON_QG_VERIFICATION_POLICY_SATISFIED)
        reasons.append("All verification signals pass policy thresholds")
        score = _calculate_policy_score(DECISION_VERIFIED, safety, visual, geo, issue)
        trust_score = round(score / 100.0, 3)
        logger.info(f"[QualityGate] report={report_id} → VERIFIED | policy_score={score} trust_score={trust_score}")
        return {
            "verification_decision": DECISION_VERIFIED,
            "policy_version": QUALITY_GATE_POLICY_VERSION,
            "reason_codes": reason_codes,
            "reasons": reasons,
            "decision_reasons": reasons,
            "evidence_summary": evidence_summary,
            "policy_score": score,
            "trust_score": trust_score,
            "requires_manual_review": False,
        }

    # Default fallback
    reason_codes.append(REASON_QG_MINIMUM_EVIDENCE_NOT_MET)
    reasons.append("Minimum evidence requirements for automated verification were not met")
    score = _calculate_policy_score(DECISION_PENDING_MANUAL_REVIEW, safety, visual, geo, issue)
    return {
        "verification_decision": DECISION_PENDING_MANUAL_REVIEW,
        "policy_version": QUALITY_GATE_POLICY_VERSION,
        "reason_codes": reason_codes,
        "reasons": reasons,
        "decision_reasons": reasons,
        "evidence_summary": evidence_summary,
        "policy_score": score,
        "trust_score": round(score / 100.0, 3),
        "requires_manual_review": True,
    }
