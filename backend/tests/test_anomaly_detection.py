from __future__ import annotations

from datetime import UTC, datetime, timedelta

import pytest
from app.anomaly.detector import run_anomaly_detection
from app.anomaly.scorer import evaluate_anomaly_detection_precision
from app.db.models import Entity, PositionEvent, RouteDefinition


@pytest.mark.asyncio
async def test_speed_spike_and_stale_signal_detection(async_session) -> None:
    now = datetime.now(UTC)

    # 1. Create fast entity with speed spike
    e1 = Entity(
        external_id="VEH-FAST-01",
        type="truck",
        status="active",
        last_seen_at=now,
        last_latitude=37.7749,
        last_longitude=-122.4194,
        last_speed=145.0,
        last_heading=90.0,
    )
    async_session.add(e1)
    await async_session.flush()

    evt1 = PositionEvent(
        entity_id=e1.entity_id,
        event_time=now,
        latitude=37.7749,
        longitude=-122.4194,
        speed=145.0,
        heading=90.0,
        source="api",
    )
    async_session.add(evt1)

    # 2. Create stale entity (>60 mins inactive)
    stale_time = now - timedelta(minutes=75)
    e2 = Entity(
        external_id="VEH-STALE-02",
        type="drone",
        status="active",
        last_seen_at=stale_time,
        last_latitude=37.7800,
        last_longitude=-122.4000,
        last_speed=10.0,
        last_heading=0.0,
    )
    async_session.add(e2)
    await async_session.commit()

    results = await run_anomaly_detection(async_session, window_minutes=60)
    assert len(results) >= 2

    types = {r.anomaly_type for r in results}
    assert "speed_spike" in types
    assert "stale_signal" in types


@pytest.mark.asyncio
async def test_route_corridor_deviation_detection(async_session) -> None:
    now = datetime.now(UTC)

    # 1. Add route definition
    route = RouteDefinition(
        route_name="SF-Downtown-Corridor",
        start_latitude=37.7749,
        start_longitude=-122.4194,
        end_latitude=37.7849,
        end_longitude=-122.4094,
        max_deviation_meters=100.0,
        max_speed_kms=120.0,
    )
    async_session.add(route)

    # 2. Add entity far away from corridor (dev > 100m)
    e = Entity(
        external_id="VEH-OFFROUTE-03",
        type="delivery",
        status="active",
        last_seen_at=now,
        last_latitude=37.8100,  # ~3.5km off corridor
        last_longitude=-122.3500,
        last_speed=40.0,
        last_heading=180.0,
    )
    async_session.add(e)
    await async_session.flush()

    evt = PositionEvent(
        entity_id=e.entity_id,
        event_time=now,
        latitude=37.8100,
        longitude=-122.3500,
        speed=40.0,
        heading=180.0,
    )
    async_session.add(evt)
    await async_session.commit()

    results = await run_anomaly_detection(async_session, window_minutes=60)
    dev_anomalies = [r for r in results if r.anomaly_type == "route_deviation"]
    assert len(dev_anomalies) >= 1
    assert dev_anomalies[0].anomaly_score >= 65.0


def test_anomaly_evaluation_precision_scorer() -> None:
    ground_truth = [
        {"event_id": "evt-1", "is_anomaly": True},
        {"event_id": "evt-2", "is_anomaly": True},
        {"event_id": "evt-3", "is_anomaly": False},
        {"event_id": "evt-4", "is_anomaly": False},
    ]
    predictions = [
        {"event_id": "evt-1", "is_anomaly": True},
        {"event_id": "evt-2", "is_anomaly": True},
        {"event_id": "evt-3", "is_anomaly": False},
        {"event_id": "evt-4", "is_anomaly": False},
    ]

    report = evaluate_anomaly_detection_precision(predictions, ground_truth)
    assert report.precision == 1.0
    assert report.recall == 1.0
    assert report.target_met is True
