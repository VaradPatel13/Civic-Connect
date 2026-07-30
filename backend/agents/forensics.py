"""Multimodal Image Forensics Agent for CivicConnect.

Performs civic issue validation, photo authenticity inspection, source type detection,
image quality evaluation, and duplicate detection across citizen-submitted report attachments.

Specs: docs/specs/ai-pipeline.md, docs/specs/AGENT.md
"""

from __future__ import annotations

import hashlib
import hmac
import logging
import math
import time
from typing import Any, Literal

from pydantic import BaseModel, Field

from backend.agents.state import ForensicsResult, PipelineSharedState
from backend.core.ai_engine import BaseAIEngine, UnifiedAIEngine
from backend.core.config import settings

logger = logging.getLogger(__name__)


SourceType = Literal[
    "camera_photo",
    "stock_photo",
    "internet_image",
    "downloaded_image",
    "screenshot",
    "photo_of_screen",
    "collage",
    "social_media",
    "wallpaper",
    "unknown",
]


DEFAULT_SOURCE_TYPE: SourceType = "camera_photo"


class ForensicsPydanticOutput(BaseModel):
    authentic: bool = Field(
        description="True if image appears to be a genuine camera photograph with no digital manipulation or AI generation"
    )
    supports_report: bool = Field(
        description="True if image directly supports and acts as valid visual evidence for the reported civic complaint"
    )
    reported_issue_visible: bool = Field(
        description="True if the reported civic issue (e.g. pothole, garbage, leak) is clearly visible in the photo"
    )
    issue_category_match: bool = Field(
        description="True if the visual evidence in the image matches the reported issue category"
    )
    source_type: SourceType = Field(
        default=DEFAULT_SOURCE_TYPE,
        description="Detected origin of the media attachment (e.g., camera_photo, stock_photo, screenshot, etc.)",
    )
    quality_ok: bool = Field(
        description="True if resolution, lighting, focus, and framing allow clear inspection of the reported issue"
    )
    ai_generated: bool = Field(
        default=False,
        description="True if image shows synthetic AI generation signatures (diffusion artifacts, malformed geometry)",
    )
    manipulated: bool = Field(
        default=False,
        description="True if image shows digital editing, splicing, cloning, or compositing boundaries",
    )
    confidence: float = Field(description="Forensic confidence score between 0.0 and 1.0")
    reason: str = Field(description="Detailed forensic explanation of findings and visual inspection notes")
    duplicate_detected: bool = Field(
        default=False, description="True if an identical or near-identical image exists in the system"
    )
    matching_report_id: str | None = Field(
        default=None,
        description="UUID string of existing matching report if duplicate is detected, else None",
    )


def haversine_distance_meters(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """Calculates great-circle distance between two GPS coordinates in meters."""
    R = 6371000.0
    phi1 = math.radians(lat1)
    phi2 = math.radians(lat2)
    delta_phi = math.radians(lat2 - lat1)
    delta_lambda = math.radians(lon2 - lon1)
    a = math.sin(delta_phi / 2.0) ** 2 + math.cos(phi1) * math.cos(phi2) * math.sin(delta_lambda / 2.0) ** 2
    c = 2.0 * math.atan2(math.sqrt(a), math.sqrt(1.0 - a))
    return R * c


def verify_hmac_signature(sha256_hash: str, signature: str, secret_key: str) -> bool:
    """Verifies HMAC-SHA256 digital signature of image payload."""
    if not sha256_hash or not signature or not secret_key:
        return False
    expected = hmac.new(secret_key.encode("utf-8"), sha256_hash.encode("utf-8"), hashlib.sha256).hexdigest()
    return hmac.compare_digest(expected.lower(), signature.lower())


def calculate_trust_score(
    capture_source: str | None,
    source_type: str,
    authentic: bool,
    signature_valid: bool | None,
    location_uncertain: bool | None,
    capture_distance_km: float | None,
    quality_ok: bool,
    ai_generated: bool,
    manipulated: bool,
    supports_report: bool,
) -> int:
    """Calculates evidence trust score (0-100) based on origin, integrity, and spatial metadata."""
    if ai_generated or manipulated or not authentic or source_type == "stock_photo":
        return 0

    if capture_source == "camera":
        score = 100
    elif capture_source == "gallery":
        score = 70
    elif source_type == "downloaded_image":
        score = 20
    else:
        score = 80

    if signature_valid is False:
        score -= 50
    if location_uncertain is True:
        score -= 15
    if capture_distance_km is not None and capture_distance_km > 5.0:
        score -= 30
    if not quality_ok:
        score -= 15
    if not supports_report:
        score -= 40

    return max(0, min(100, score))


class ForensicsAgent:
    """Multimodal agent that performs comprehensive image authenticity, civic evidence validation, and duplicate detection."""

    def __init__(self, ai_engine: BaseAIEngine | UnifiedAIEngine | Any | None = None) -> None:
        self.ai_engine: BaseAIEngine | Any = ai_engine or UnifiedAIEngine(provider="nvidia_nim")

    async def process(self, state: PipelineSharedState) -> dict[str, Any]:
        """Executes Image Forensics node logic for LangGraph workflow using multimodal visual inspection."""
        start_time = time.time()
        raw_payload = state.get("raw_payload") or {}
        media_urls: list[str] = raw_payload.get("media_urls") or []

        if not media_urls:
            logger.info("[Forensics] Report contains no image attachments. Defaulting to empty media validation.")
            result: ForensicsResult = {
                "authentic": True,
                "supports_report": True,
                "reported_issue_visible": False,
                "issue_category_match": True,
                "source_type": "unknown",
                "quality_ok": True,
                "ai_generated": False,
                "manipulated": False,
                "confidence": 1.0,
                "reason": "No media attachments present in report payload",
                "duplicate_detected": False,
                "matching_report_id": None,
                "capture_source": None,
                "signature_valid": None,
                "location_uncertain": None,
                "capture_distance_km": None,
                "trust_score": 100,
            }
            return {"agent_outputs": {"forensics": result}}

        report_id = state.get("report_id") or "UNKNOWN"
        title = raw_payload.get("title") or "Unspecified Title"
        description = state.get("sanitised_text") or raw_payload.get("description") or "Unspecified Description"
        category = raw_payload.get("category") or "Unspecified Category"
        urgency = raw_payload.get("urgency") or "Unspecified Urgency"
        address = raw_payload.get("address") or "Unspecified Location"
        lat = raw_payload.get("latitude", "N/A")
        lon = raw_payload.get("longitude", "N/A")

        prompt = (
            f"CIVIC REPORT FOR FORENSIC INSPECTION:\n"
            f"- Report ID: {report_id}\n"
            f"- Title: {title}\n"
            f"- Description: {description}\n"
            f"- Category: {category}\n"
            f"- Urgency: {urgency}\n"
            f"- Location: {address} (Lat: {lat}, Lon: {lon})\n"
            f"- Media Attachments: {media_urls}\n\n"
            f"INSPECTION TASK:\n"
            f"Inspect attached image(s) and evaluate:\n"
            f"1. Civic Issue Visibility & Match: Is the reported problem visible? Does it match the stated category? "
            f"Reject selfies, pets, posing people, random interiors, memes, advertisements, documents, logos, or unrelated objects.\n"
            f"2. Authenticity & AI/Manipulation: Check for diffusion artifacts, impossible geometry, malformed objects, inconsistent lighting, cloning, or editing boundaries.\n"
            f"3. Source Type: Identify source (camera_photo, stock_photo, internet_image, downloaded_image, screenshot, photo_of_screen, collage, social_media, wallpaper, unknown). "
            f"If image is from a stock library (Unsplash, Pexels, Shutterstock, etc.), set supports_report = false.\n"
            f"4. Image Quality: Verify if lighting, focus, and resolution allow clear inspection.\n"
            f"5. Duplicate Detection: Set duplicate_detected and matching_report_id if duplicate exists."
        )

        system_prompt = (
            "You are the PMC Senior Media Forensics & Visual Evidence Auditor.\n"
            "Evaluate citizen-submitted report photos for authenticity, quality, origin, and visual support of civic complaints.\n\n"
            "RULES:\n"
            "- Stock photos (Unsplash, Pexels, Shutterstock, etc.) are INVALID evidence -> supports_report = false.\n"
            "- Irrelevant photos (selfies, pets, posing people, memes, screenshots, indoor photos, ads) are INVALID -> supports_report = false.\n"
            "- AI-generated or digitally manipulated photos are INVALID -> authentic = false, supports_report = false.\n"
            "- Do NOT fabricate metadata. Evaluate visual evidence directly.\n"
            "- Maintain strict civic evidence standards."
        )

        try:
            parsed, exec_ms, tokens, model_name = await self.ai_engine.generate_structured(
                prompt=prompt,
                response_model=ForensicsPydanticOutput,
                system_prompt=system_prompt,
                temperature=0.1,
                image_urls=media_urls,
            )

            # Stock photo enforcement rule
            supports_rep = parsed.supports_report
            if parsed.source_type == "stock_photo":
                supports_rep = False

            result: ForensicsResult = {
                "authentic": parsed.authentic and not (parsed.ai_generated or parsed.manipulated),
                "supports_report": supports_rep,
                "reported_issue_visible": parsed.reported_issue_visible,
                "issue_category_match": parsed.issue_category_match,
                "source_type": str(parsed.source_type),
                "quality_ok": parsed.quality_ok,
                "ai_generated": parsed.ai_generated,
                "manipulated": parsed.manipulated,
                "confidence": parsed.confidence,
                "reason": parsed.reason,
                "duplicate_detected": parsed.duplicate_detected,
                "matching_report_id": parsed.matching_report_id if parsed.duplicate_detected else None,
                "capture_source": None,
                "signature_valid": None,
                "location_uncertain": None,
                "capture_distance_km": None,
            }

            # Levels 1-9 Secure Metadata Inspection
            photo_meta_list = raw_payload.get("photo_metadata") or []
            if photo_meta_list:
                for meta in photo_meta_list:
                    if isinstance(meta, dict):
                        # Level 1 & 9: Anti-Gallery capture source check
                        c_src = meta.get("capture_source")
                        if c_src:
                            result["capture_source"] = c_src
                            if c_src == "gallery":
                                result["supports_report"] = False
                                result["source_type"] = "downloaded_image"
                                result["reason"] += " | Gallery upload detected — live app camera capture required for evidence."

                        # Level 4: Digital Signature & SHA256 Hash Tamper Verification
                        sha256 = meta.get("sha256_hash")
                        sig = meta.get("hmac_signature")
                        if sha256 and sig:
                            secret = getattr(settings, "jwt_secret_key", "civicconnect_secret_key")
                            is_valid = verify_hmac_signature(sha256, sig, secret)
                            result["signature_valid"] = is_valid
                            if not is_valid:
                                result["authentic"] = False
                                result["manipulated"] = True
                                result["reason"] += " | Digital signature validation failed (image tampered after capture)."

                        # Level 7: GPS Accuracy Validation
                        accuracy = meta.get("gps_accuracy_m")
                        if accuracy is not None and float(accuracy) > 100.0:
                            result["location_uncertain"] = True
                            result["reason"] += f" | GPS accuracy {accuracy}m > 100m (location uncertain)."

                        # Level 8: Compare capture location with report location
                        cap_lat = meta.get("latitude")
                        cap_lon = meta.get("longitude")
                        rep_lat_val = raw_payload.get("latitude")
                        rep_lon_val = raw_payload.get("longitude")
                        if (
                            cap_lat is not None
                            and cap_lon is not None
                            and rep_lat_val is not None
                            and rep_lon_val is not None
                        ):
                            try:
                                rep_lat = float(rep_lat_val)
                                rep_lon = float(rep_lon_val)
                                dist_m = haversine_distance_meters(float(cap_lat), float(cap_lon), rep_lat, rep_lon)
                                dist_km = dist_m / 1000.0
                                result["capture_distance_km"] = round(dist_km, 2)
                                if dist_m > 5000.0:
                                    result["supports_report"] = False
                                    result["issue_category_match"] = False
                                    result["reason"] += f" | Photo capture location differs from report location ({dist_km:.1f} km away)."
                            except (ValueError, TypeError):
                                pass

            result["trust_score"] = calculate_trust_score(
                capture_source=result.get("capture_source"),
                source_type=result.get("source_type", "unknown"),
                authentic=result.get("authentic", False),
                signature_valid=result.get("signature_valid"),
                location_uncertain=result.get("location_uncertain"),
                capture_distance_km=result.get("capture_distance_km"),
                quality_ok=result.get("quality_ok", True),
                ai_generated=result.get("ai_generated", False),
                manipulated=result.get("manipulated", False),
                supports_report=result.get("supports_report", True),
            )

            execution_ms = (time.time() - start_time) * 1000.0
            logger.info(
                f"[Forensics] Completed image analysis in {execution_ms:.2f}ms via {model_name}. "
                f"Authentic: {result['authentic']}, TrustScore: {result['trust_score']}, Source: {result['source_type']}"
            )
            return {"agent_outputs": {"forensics": result}}

        except Exception as err:
            logger.warning(f"[Forensics] Forensics analysis error ({err}). Failing SAFE — marking for manual review.")
            fallback: ForensicsResult = {
                "authentic": False,
                "supports_report": False,
                "reported_issue_visible": False,
                "issue_category_match": False,
                "source_type": "unknown",
                "quality_ok": False,
                "ai_generated": False,
                "manipulated": False,
                "confidence": 0.0,
                "reason": "Forensics unavailable - manual review required",
                "duplicate_detected": False,
                "matching_report_id": None,
                "capture_source": None,
                "signature_valid": None,
                "location_uncertain": None,
                "capture_distance_km": None,
                "trust_score": 0,
            }
            return {"agent_outputs": {"forensics": fallback}}
