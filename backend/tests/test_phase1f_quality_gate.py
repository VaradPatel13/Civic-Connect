"""Phase 1F — Trust / Quality Gate Policy Engine Tests.

Tests explicit policy ladder, decision precedence, reason codes, failure safety,
and regression invariants for CivicConnect Phase 1F.
"""

from __future__ import annotations

import math
from typing import Any

import pytest

from backend.agents.quality_gate import (
    DECISION_PENDING_MANUAL_REVIEW,
    DECISION_REJECTED,
    DECISION_VERIFIED,
    QUALITY_GATE_POLICY_VERSION,
    REASON_QG_GEO_UNAVAILABLE,
    REASON_QG_GEO_UNCONFIRMED,
    REASON_QG_HEURISTIC_ONLY_ISSUE,
    REASON_QG_INVALID_COORDINATES,
    REASON_QG_INVALID_SIGNATURE,
    REASON_QG_ISSUE_AMBIGUOUS,
    REASON_QG_ISSUE_LOW_CONFIDENCE,
    REASON_QG_ISSUE_UNAVAILABLE,
    REASON_QG_MALFORMED_COMPONENT,
    REASON_QG_MINIMUM_EVIDENCE_NOT_MET,
    REASON_QG_MISSING_COMPONENT,
    REASON_QG_NON_CIVIC,
    REASON_QG_OUTSIDE_JURISDICTION,
    REASON_QG_SAFETY_BLOCK,
    REASON_QG_SAFETY_UNAVAILABLE,
    REASON_QG_VERIFICATION_POLICY_SATISFIED,
    REASON_QG_VISUAL_CONTRADICTION,
    REASON_QG_VISUAL_LOW_CONFIDENCE,
    REASON_QG_VISUAL_RISK,
    REASON_QG_VISUAL_UNAVAILABLE,
    evaluate_quality_gate,
)


@pytest.fixture(autouse=True)
def setup_and_cleanup_db():
    """Bypass autouse database setup for pure Quality Gate policy unit tests."""
    yield


def _make_golden_evidence() -> dict[str, Any]:
    """Helper returning a canonical golden VERIFIED evidence bundle."""
    return {
        "safety": {
            "analysis_status": "SUCCESS",
            "clean": True,
            "flags": [],
            "confidence": 0.99,
        },
        "visual_verification": {
            "analysis_status": "SUCCESS",
            "supports_report": True,
            "evidence_confidence": 0.90,
            "risk_flags": [],
            "signals": {
                "signature_valid": True,
                "exif_present": True,
                "screenshot_suspected": False,
            },
        },
        "geo_validation": {
            "analysis_status": "SUCCESS",
            "coordinates_valid": True,
            "municipality_matched": True,
            "boundary_matched": True,
            "near_boundary": False,
            "confidence": 0.95,
            "signals": {},
        },
        "issue_intelligence": {
            "analysis_status": "SUCCESS",
            "civic_relevance": True,
            "category": "ROADS",
            "confidence": 0.85,
            "details": {
                "analysis_source": "MODEL",
            },
            "ambiguous_issue": False,
            "insufficient_information": False,
        },
    }


@pytest.mark.asyncio
async def test_golden_verified_report():
    """Verify canonical high-quality report receives VERIFIED decision and policy score."""
    evidence = _make_golden_evidence()
    res = evaluate_quality_gate(evidence, report_id="rep-101")

    assert res["verification_decision"] == DECISION_VERIFIED
    assert res["policy_version"] == QUALITY_GATE_POLICY_VERSION
    assert REASON_QG_VERIFICATION_POLICY_SATISFIED in res["reason_codes"]
    assert res["requires_manual_review"] is False
    assert res["trust_score"] >= 0.80


@pytest.mark.asyncio
async def test_safety_unavailable_routes_to_manual_review():
    """Verify safety provider failure routes to PENDING_MANUAL_REVIEW, never REJECTED."""
    evidence = _make_golden_evidence()
    evidence["safety"] = {
        "analysis_status": "UNAVAILABLE",
        "clean": None,
        "flags": ["safety_service_timeout"],
    }
    res = evaluate_quality_gate(evidence)

    assert res["verification_decision"] == DECISION_PENDING_MANUAL_REVIEW
    assert REASON_QG_SAFETY_UNAVAILABLE in res["reason_codes"]
    assert res["requires_manual_review"] is True


@pytest.mark.asyncio
async def test_visual_unavailable_routes_to_manual_review():
    """Verify visual provider failure routes to manual review when image is attached."""
    evidence = _make_golden_evidence()
    evidence["visual_verification"] = {
        "analysis_status": "UNAVAILABLE",
        "supports_report": None,
        "evidence_confidence": None,
    }
    res = evaluate_quality_gate(evidence)

    assert res["verification_decision"] == DECISION_PENDING_MANUAL_REVIEW
    assert REASON_QG_VISUAL_UNAVAILABLE in res["reason_codes"]


@pytest.mark.asyncio
async def test_issue_unavailable_routes_to_manual_review():
    """Verify issue intelligence failure routes to manual review."""
    evidence = _make_golden_evidence()
    evidence["issue_intelligence"] = {
        "analysis_status": "UNAVAILABLE",
        "confidence": None,
    }
    res = evaluate_quality_gate(evidence)

    assert res["verification_decision"] == DECISION_PENDING_MANUAL_REVIEW
    assert REASON_QG_ISSUE_UNAVAILABLE in res["reason_codes"]


@pytest.mark.asyncio
async def test_geo_unavailable_routes_to_manual_review():
    """Verify geo validator failure routes to manual review."""
    evidence = _make_golden_evidence()
    evidence["geo_validation"] = {
        "analysis_status": "UNAVAILABLE",
        "coordinates_valid": None,
    }
    res = evaluate_quality_gate(evidence)

    assert res["verification_decision"] == DECISION_PENDING_MANUAL_REVIEW
    assert REASON_QG_GEO_UNAVAILABLE in res["reason_codes"]


@pytest.mark.asyncio
async def test_invalid_coordinates_rejected():
    """Verify structurally invalid GPS coordinates result in REJECTED decision."""
    evidence = _make_golden_evidence()
    evidence["geo_validation"]["coordinates_valid"] = False
    res = evaluate_quality_gate(evidence)

    assert res["verification_decision"] == DECISION_REJECTED
    assert REASON_QG_INVALID_COORDINATES in res["reason_codes"]


@pytest.mark.asyncio
async def test_outside_jurisdiction_rejected():
    """Verify confirmed out-of-jurisdiction report results in REJECTED decision."""
    evidence = _make_golden_evidence()
    evidence["geo_validation"]["municipality_matched"] = False
    evidence["geo_validation"]["confidence"] = 0.90
    res = evaluate_quality_gate(evidence)

    assert res["verification_decision"] == DECISION_REJECTED
    assert REASON_QG_OUTSIDE_JURISDICTION in res["reason_codes"]


@pytest.mark.asyncio
async def test_non_civic_issue_rejected():
    """Verify high-confidence non-civic private report results in REJECTED decision."""
    evidence = _make_golden_evidence()
    evidence["issue_intelligence"]["civic_relevance"] = False
    evidence["issue_intelligence"]["confidence"] = 0.85
    evidence["issue_intelligence"]["details"]["analysis_source"] = "MODEL"
    res = evaluate_quality_gate(evidence)

    assert res["verification_decision"] == DECISION_REJECTED
    assert REASON_QG_NON_CIVIC in res["reason_codes"]


@pytest.mark.asyncio
async def test_ambiguous_issue_manual_review():
    """Verify ambiguous issue description triggers manual review, not rejection."""
    evidence = _make_golden_evidence()
    evidence["issue_intelligence"]["ambiguous_issue"] = True
    res = evaluate_quality_gate(evidence)

    assert res["verification_decision"] == DECISION_PENDING_MANUAL_REVIEW
    assert REASON_QG_ISSUE_AMBIGUOUS in res["reason_codes"]


@pytest.mark.asyncio
async def test_deterministic_only_issue_manual_review():
    """Verify deterministic fallback classification requires manual review."""
    evidence = _make_golden_evidence()
    evidence["issue_intelligence"]["details"]["analysis_source"] = "DETERMINISTIC_ONLY"
    res = evaluate_quality_gate(evidence)

    assert res["verification_decision"] == DECISION_PENDING_MANUAL_REVIEW
    assert REASON_QG_HEURISTIC_ONLY_ISSUE in res["reason_codes"]


@pytest.mark.asyncio
async def test_strong_visual_contradiction_manual_review():
    """Verify text-image contradiction triggers manual review."""
    evidence = _make_golden_evidence()
    evidence["visual_verification"]["supports_report"] = False
    evidence["visual_verification"]["evidence_confidence"] = 0.85
    res = evaluate_quality_gate(evidence)

    assert res["verification_decision"] == DECISION_PENDING_MANUAL_REVIEW
    assert REASON_QG_VISUAL_CONTRADICTION in res["reason_codes"]


@pytest.mark.asyncio
async def test_dark_unclear_image_manual_review():
    """Verify dark or unclear image (supports_report=None) triggers manual review."""
    evidence = _make_golden_evidence()
    evidence["visual_verification"]["supports_report"] = None
    evidence["visual_verification"]["evidence_confidence"] = 0.30
    res = evaluate_quality_gate(evidence)

    assert res["verification_decision"] == DECISION_PENDING_MANUAL_REVIEW
    assert REASON_QG_VISUAL_LOW_CONFIDENCE in res["reason_codes"]


@pytest.mark.asyncio
async def test_no_exif_alone_does_not_reject():
    """Verify missing EXIF metadata alone does not prevent VERIFIED status."""
    evidence = _make_golden_evidence()
    evidence["visual_verification"]["signals"]["exif_present"] = False
    res = evaluate_quality_gate(evidence)

    assert res["verification_decision"] == DECISION_VERIFIED


@pytest.mark.asyncio
async def test_screenshot_suspected_manual_review():
    """Verify screenshot detection flag triggers manual review."""
    evidence = _make_golden_evidence()
    evidence["visual_verification"]["risk_flags"] = ["photo_of_screen_detected"]
    evidence["visual_verification"]["signals"]["screenshot_suspected"] = True
    res = evaluate_quality_gate(evidence)

    assert res["verification_decision"] == DECISION_PENDING_MANUAL_REVIEW
    assert REASON_QG_VISUAL_RISK in res["reason_codes"]


@pytest.mark.asyncio
async def test_invalid_signature_manual_review():
    """Verify failed HMAC signature triggers QG_INVALID_SIGNATURE and manual review."""
    evidence = _make_golden_evidence()
    evidence["visual_verification"]["signals"]["signature_valid"] = False
    res = evaluate_quality_gate(evidence)

    assert res["verification_decision"] == DECISION_PENDING_MANUAL_REVIEW
    assert REASON_QG_INVALID_SIGNATURE in res["reason_codes"]


@pytest.mark.asyncio
async def test_missing_signature_vs_invalid_signature():
    """Verify missing signature (None) is treated differently from invalid signature (False)."""
    evidence_none = _make_golden_evidence()
    evidence_none["visual_verification"]["signals"]["signature_valid"] = None
    res_none = evaluate_quality_gate(evidence_none)

    evidence_false = _make_golden_evidence()
    evidence_false["visual_verification"]["signals"]["signature_valid"] = False
    res_false = evaluate_quality_gate(evidence_false)

    assert REASON_QG_INVALID_SIGNATURE not in res_none["reason_codes"]
    assert REASON_QG_INVALID_SIGNATURE in res_false["reason_codes"]


@pytest.mark.asyncio
async def test_duplicate_image_manual_review():
    """Verify duplicate image detection triggers visual risk review."""
    evidence = _make_golden_evidence()
    evidence["visual_verification"]["signals"]["perceptual_duplicate_found"] = True
    res = evaluate_quality_gate(evidence)

    assert res["verification_decision"] == DECISION_PENDING_MANUAL_REVIEW
    assert REASON_QG_VISUAL_RISK in res["reason_codes"]


@pytest.mark.asyncio
async def test_near_boundary_manual_review():
    """Verify location near ward boundary triggers geo unconfirmed review."""
    evidence = _make_golden_evidence()
    evidence["geo_validation"]["near_boundary"] = True
    res = evaluate_quality_gate(evidence)

    assert res["verification_decision"] == DECISION_PENDING_MANUAL_REVIEW
    assert REASON_QG_GEO_UNCONFIRMED in res["reason_codes"]


@pytest.mark.asyncio
async def test_prompt_injection_suspected_only_not_rejected():
    """Verify injection_suspected=True with clean=True does NOT reject report."""
    evidence = _make_golden_evidence()
    evidence["safety"]["injection_suspected"] = True
    evidence["safety"]["injection_detected"] = False
    evidence["safety"]["clean"] = True
    res = evaluate_quality_gate(evidence)

    assert res["verification_decision"] == DECISION_VERIFIED


@pytest.mark.asyncio
async def test_missing_component_manual_review():
    """Verify missing required agent branch yields QG_MISSING_COMPONENT."""
    evidence = _make_golden_evidence()
    del evidence["geo_validation"]
    res = evaluate_quality_gate(evidence)

    assert res["verification_decision"] == DECISION_PENDING_MANUAL_REVIEW
    assert REASON_QG_MISSING_COMPONENT in res["reason_codes"]


@pytest.mark.asyncio
async def test_malformed_component_manual_review():
    """Verify non-dict component yield QG_MALFORMED_COMPONENT."""
    evidence = _make_golden_evidence()
    evidence["visual_verification"] = "not_a_dict"
    res = evaluate_quality_gate(evidence)

    assert res["verification_decision"] == DECISION_PENDING_MANUAL_REVIEW
    assert REASON_QG_MALFORMED_COMPONENT in res["reason_codes"]


@pytest.mark.asyncio
async def test_confidence_attacks_resilience():
    """Verify malformed confidence values (NaN, infinity, strings) do not crash gate."""
    evidence = _make_golden_evidence()
    evidence["issue_intelligence"]["confidence"] = float("nan")
    evidence["visual_verification"]["evidence_confidence"] = float("inf")
    res = evaluate_quality_gate(evidence)

    assert res["verification_decision"] == DECISION_PENDING_MANUAL_REVIEW


@pytest.mark.asyncio
async def test_state_injection_resilience():
    """Verify untrusted nested decision values in payload are ignored by gate."""
    evidence = _make_golden_evidence()
    evidence["issue_intelligence"]["verification_decision"] = "VERIFIED"
    evidence["issue_intelligence"]["policy_score"] = 100
    evidence["geo_validation"]["coordinates_valid"] = False

    res = evaluate_quality_gate(evidence)
    # Invalid coordinates MUST override any attempted state injection
    assert res["verification_decision"] == DECISION_REJECTED


@pytest.mark.asyncio
async def test_decision_determinism():
    """Verify quality gate engine is 100% deterministic across multiple runs."""
    evidence = _make_golden_evidence()
    res1 = evaluate_quality_gate(evidence)
    res2 = evaluate_quality_gate(evidence)

    assert res1 == res2


@pytest.mark.asyncio
async def test_no_confidence_averaging_regression():
    """Verify high confidence scores in other branches cannot override visual contradiction."""
    evidence = _make_golden_evidence()
    evidence["safety"]["confidence"] = 1.0
    evidence["issue_intelligence"]["confidence"] = 1.0
    evidence["geo_validation"]["confidence"] = 1.0
    evidence["visual_verification"]["supports_report"] = False
    evidence["visual_verification"]["evidence_confidence"] = 0.90

    res = evaluate_quality_gate(evidence)
    assert res["verification_decision"] != DECISION_VERIFIED


@pytest.mark.asyncio
async def test_critical_urgency_does_not_boost_trust():
    """Verify critical severity/urgency does not bypass quality gate thresholds."""
    evidence = _make_golden_evidence()
    evidence["issue_intelligence"]["severity"] = "CRITICAL"
    evidence["issue_intelligence"]["urgency"] = "CRITICAL"
    evidence["issue_intelligence"]["confidence"] = 0.20  # Low confidence

    res = evaluate_quality_gate(evidence)
    assert res["verification_decision"] == DECISION_PENDING_MANUAL_REVIEW


@pytest.mark.asyncio
async def test_policy_score_independence():
    """Verify decision is determined by explicit rules, NOT numeric score."""
    # Case 1: Max score 100 but invalid coordinates -> REJECTED
    evidence_bad = _make_golden_evidence()
    evidence_bad["geo_validation"]["coordinates_valid"] = False

    res_bad = evaluate_quality_gate(evidence_bad)
    assert res_bad["verification_decision"] == DECISION_REJECTED
    assert res_bad["policy_score"] == 0

    # Case 2: Scores differ but policy decision is identical (PENDING_MANUAL_REVIEW)
    ev1 = _make_golden_evidence()
    ev1["issue_intelligence"]["ambiguous_issue"] = True

    ev2 = _make_golden_evidence()
    ev2["issue_intelligence"]["ambiguous_issue"] = True
    ev2["visual_verification"]["risk_flags"] = ["photo_of_screen_detected"]
    ev2["visual_verification"]["signals"]["screenshot_suspected"] = True

    res1 = evaluate_quality_gate(ev1)
    res2 = evaluate_quality_gate(ev2)

    assert res1["verification_decision"] == DECISION_PENDING_MANUAL_REVIEW
    assert res2["verification_decision"] == DECISION_PENDING_MANUAL_REVIEW
    assert res1["policy_score"] != res2["policy_score"]


@pytest.mark.asyncio
async def test_safety_profanity_routes_to_manual_review_not_rejected():
    """Verify profanity/toxicity (clean=False without severe abuse/spam/code attack) triggers manual review, not REJECTED."""
    evidence = _make_golden_evidence()
    evidence["safety"]["clean"] = False
    evidence["safety"]["flags"] = ["profanity", "toxicity"]
    evidence["safety"]["signals"] = {
        "abuse": {"detected": False},
        "spam": {"detected": False},
        "deterministic_signals": [],
    }

    res = evaluate_quality_gate(evidence)
    assert res["verification_decision"] == DECISION_PENDING_MANUAL_REVIEW
    assert "QG_SAFETY_REVIEW" in res["reason_codes"]


@pytest.mark.asyncio
async def test_authoritative_geo_override_rejects_approximate():
    """Verify authoritative PostGIS mismatch (municipality_matched=False) overrides approximate regional envelope match."""
    evidence = _make_golden_evidence()
    evidence["geo_validation"]["municipality_matched"] = False
    evidence["geo_validation"]["confidence"] = 0.90
    evidence["geo_validation"]["signals"] = {"approximate_boundary_match": True}
    evidence["geo_validation"]["regional_envelope_matched"] = True

    res = evaluate_quality_gate(evidence)
    assert res["verification_decision"] == DECISION_REJECTED
    assert REASON_QG_OUTSIDE_JURISDICTION in res["reason_codes"]


@pytest.mark.asyncio
async def test_approximate_geo_provisional_verified():
    """Verify provisional regional candidate match (municipality_matched=None, approx=True) reaches VERIFIED."""
    evidence = _make_golden_evidence()
    evidence["geo_validation"]["municipality_matched"] = None
    evidence["geo_validation"]["boundary_matched"] = None
    evidence["geo_validation"]["signals"] = {"approximate_boundary_match": True}

    res = evaluate_quality_gate(evidence)
    assert res["verification_decision"] == DECISION_VERIFIED

