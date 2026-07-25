"""Live Interactive Execution Script for CivicConnect Multi-Agent Pipeline.

Executes real live report triage against NVIDIA NIM AI infrastructure.
Usage:
    python -m backend.scripts.run_live_test "Severe pothole and waterlogging near Kothrud stand" 18.50 73.80
"""

import json
import logging
import os
import sys
import uuid

# Force UTF-8 stdout encoding for Windows terminals
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")  # type: ignore

from backend.agents.pipeline import create_civic_pipeline_graph
from backend.core.config import settings

# Setup clean console logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    datefmt="%H:%M:%S",
)


def run_live_triage(
    description: str,
    latitude: float = 18.55,
    longitude: float = 73.80,
) -> None:
    """Executes live report triage through the multi-agent pipeline graph."""
    print("\n" + "=" * 80)
    print("CIVICCONNECT LIVE MULTI-AGENT TRIAGE ENGINE")
    print(f"Provider: {settings.ai_provider.upper()} | Key Configured: {'YES' if settings.nvidia_api_key else 'NO'}")
    print("=" * 80)

    report_id = f"REP-{uuid.uuid4().hex[:8].upper()}"
    trace_id = f"TRACE-{uuid.uuid4().hex[:8].upper()}"

    initial_state = {
        "report_id": report_id,
        "trace_id": trace_id,
        "raw_payload": {
            "description": description,
            "latitude": latitude,
            "longitude": longitude,
            "media_urls": [],
        },
    }

    print(f"\n[INGESTED REPORT]")
    print(f"  * ID:          {report_id}")
    print(f"  * Description: \"{description}\"")
    print(f"  * GPS Coords:  ({latitude}, {longitude})")
    print("\nExecuting 9-Agent LangGraph Pipeline...\n")

    graph = create_civic_pipeline_graph()
    final_state = graph.invoke(initial_state)

    print("\n" + "=" * 80)
    print("AGENT PIPELINE EXECUTION COMPLETED SUCCESSFULLY")
    print("=" * 80)

    outputs = final_state.get("agent_outputs", {})

    print(json.dumps(outputs, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    if len(sys.argv) > 1:
        desc = sys.argv[1]
        lat = float(sys.argv[2]) if len(sys.argv) > 2 else 18.55
        lon = float(sys.argv[3]) if len(sys.argv) > 3 else 73.80
    else:
        desc = input("\nEnter citizen report description: ").strip() or "Severe road damage and pothole on main avenue near Baner."
        lat_input = input("Enter Latitude [default: 18.55]: ").strip()
        lon_input = input("Enter Longitude [default: 73.80]: ").strip()
        lat = float(lat_input) if lat_input else 18.55
        lon = float(lon_input) if lon_input else 73.80

    run_live_triage(desc, lat, lon)
