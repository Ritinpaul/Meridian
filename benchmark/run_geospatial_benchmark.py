from __future__ import annotations

import asyncio
import json
import sys
import time
from datetime import UTC, datetime
from pathlib import Path

# Ensure backend dir is in sys.path
backend_path = Path(__file__).parent.parent / "backend"
if str(backend_path) not in sys.path:
    sys.path.insert(0, str(backend_path))

from app.anomaly.detector import run_anomaly_detection
from app.db.models import Entity, PositionEvent, RouteDefinition
from app.db.session import SessionLocal, init_db
from app.nl_query.service import generate_operations_summary, process_natural_language_query


async def run_benchmark() -> dict:
    print("[+] Starting Meridian Geospatial Benchmark Suite...")
    await init_db()

    # 1. High-Throughput Telemetry Ingestion Benchmark (5,000 synthetic records)
    batch_size = 5000
    now = datetime.now(UTC).replace(tzinfo=None)

    entities = [
        Entity(
            external_id=f"BENCH-VEH-{i:04d}",
            type="vehicle",
            status="active" if i % 10 != 0 else "warning",
            last_seen_at=now,
            last_latitude=37.70 + (i % 50) * 0.005,
            last_longitude=-122.50 + Math_floor_div(i, 50) * 0.005,
            last_speed=40.0 + (i % 95),
            last_heading=(i * 23) % 360,
        )
        for i in range(batch_size)
    ]

    t0 = time.perf_counter()
    async with SessionLocal() as session:
        session.add_all(entities)
        await session.commit()
    ingest_time_sec = time.perf_counter() - t0
    msgs_per_sec = round(batch_size / ingest_time_sec, 2)
    print(f"  [1] Ingest Benchmark: {batch_size} records in {ingest_time_sec:.3f}s ({msgs_per_sec} msgs/sec)")

    # 2. Anomaly Detection Latency Benchmark
    t1 = time.perf_counter()
    async with SessionLocal() as session:
        anomalies = await run_anomaly_detection(session, window_minutes=60)
    anomaly_time_ms = round((time.perf_counter() - t1) * 1000.0, 2)
    print(f"  [2] Anomaly Engine Latency: {len(anomalies)} anomalies detected in {anomaly_time_ms}ms")

    # 3. Natural Language Query Latency Benchmark
    t2 = time.perf_counter()
    async with SessionLocal() as session:
        nl_res = await process_natural_language_query(session, "Which vehicles exceeded 90 km/h speed limit?")
    nl_time_ms = round((time.perf_counter() - t2) * 1000.0, 2)
    print(f"  [3] NL Query Translation Latency: {nl_res['row_count']} rows in {nl_time_ms}ms")

    results = {
        "timestamp": now.isoformat(),
        "batch_size": batch_size,
        "ingest_throughput_msgs_per_sec": msgs_per_sec,
        "ingest_total_seconds": round(ingest_time_sec, 3),
        "anomaly_detection_latency_ms": anomaly_time_ms,
        "nl_query_translation_latency_ms": nl_time_ms,
        "performance_targets_met": {
            "throughput_high": msgs_per_sec >= 1000.0,
            "anomaly_latency_fast": anomaly_time_ms <= 250.0,
            "nl_query_latency_fast": nl_time_ms <= 100.0,
        },
    }

    results_path = Path(__file__).parent / "results.json"
    results_path.write_text(json.dumps(results, indent=2), encoding="utf-8")
    print(f"[OK] Benchmark Complete! Results saved to {results_path}")
    return results


def Math_floor_div(a: int, b: int) -> int:
    return a // b


if __name__ == "__main__":
    asyncio.run(run_benchmark())
