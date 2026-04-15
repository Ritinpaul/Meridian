from __future__ import annotations

import math
from datetime import UTC, datetime, timedelta
from dataclasses import dataclass
from uuid import uuid4

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import AnomalyEvent, Entity, PositionEvent, RouteDefinition


@dataclass
class DetectedAnomalyResult:
    anomaly_id: str
    entity_id: str
    external_id: str
    anomaly_type: str
    anomaly_score: float
    reason: str
    detected_at: datetime


def _to_naive_utc(dt: datetime) -> datetime:
    return dt.replace(tzinfo=None) if dt.tzinfo else dt


async def run_anomaly_detection(
    session: AsyncSession,
    window_minutes: int = 60,
    entity_id: str | None = None,
) -> list[DetectedAnomalyResult]:
    now = datetime.now(UTC).replace(tzinfo=None)
    cutoff = now - timedelta(minutes=window_minutes)

    query = select(Entity)
    if entity_id:
        query = query.where(Entity.entity_id == entity_id)

    res = await session.execute(query)
    entities = res.scalars().all()

    routes_res = await session.execute(select(RouteDefinition))
    routes = routes_res.scalars().all()

    detected_results: list[DetectedAnomalyResult] = []

    for entity in entities:
        last_seen = _to_naive_utc(entity.last_seen_at)

        events_query = (
            select(PositionEvent)
            .where(PositionEvent.entity_id == entity.entity_id)
            .order_by(PositionEvent.event_time.asc())
        )
        events_res = await session.execute(events_query)
        all_events = events_res.scalars().all()
        events = [e for e in all_events if _to_naive_utc(e.event_time) >= cutoff]

        # 1. Stale signal check
        if last_seen < cutoff:
            stale_minutes = (now - last_seen).total_seconds() / 60.0
            score = min(99.0, 50.0 + (stale_minutes * 0.5))
            reason = f"Entity telemetry stale for {stale_minutes:.1f} minutes without heartbeat"
            anomaly = AnomalyEvent(
                anomaly_id=str(uuid4()),
                entity_id=entity.entity_id,
                anomaly_type="stale_signal",
                anomaly_score=round(score, 1),
                reason=reason,
                detected_at=now,
            )
            session.add(anomaly)
            detected_results.append(
                DetectedAnomalyResult(
                    anomaly_id=anomaly.anomaly_id,
                    entity_id=entity.entity_id,
                    external_id=entity.external_id,
                    anomaly_type=anomaly.anomaly_type,
                    anomaly_score=anomaly.anomaly_score,
                    reason=anomaly.reason,
                    detected_at=anomaly.detected_at,
                )
            )

        # 2. Event sequence analysis (Speed spike & Heading flip)
        for i in range(len(events)):
            evt = events[i]
            evt_time = _to_naive_utc(evt.event_time)

            # Speed spike
            if evt.speed is not None and evt.speed > 130.0:
                excess = evt.speed - 130.0
                score = min(99.0, 70.0 + (excess * 0.8))
                reason = f"Speed spike detected at {evt.speed:.1f} km/h (exceeds safety threshold of 130 km/h)"
                anomaly = AnomalyEvent(
                    anomaly_id=str(uuid4()),
                    entity_id=entity.entity_id,
                    anomaly_type="speed_spike",
                    anomaly_score=round(score, 1),
                    reason=reason,
                    detected_at=evt_time,
                )
                session.add(anomaly)
                detected_results.append(
                    DetectedAnomalyResult(
                        anomaly_id=anomaly.anomaly_id,
                        entity_id=entity.entity_id,
                        external_id=entity.external_id,
                        anomaly_type=anomaly.anomaly_type,
                        anomaly_score=anomaly.anomaly_score,
                        reason=anomaly.reason,
                        detected_at=anomaly.detected_at,
                    )
                )

            # Consecutive heading flip check
            if i > 0:
                prev_evt = events[i - 1]
                prev_time = _to_naive_utc(prev_evt.event_time)
                time_delta_sec = (evt_time - prev_time).total_seconds()
                if (
                    time_delta_sec <= 10.0
                    and evt.heading is not None
                    and prev_evt.heading is not None
                    and evt.speed is not None
                    and evt.speed > 30.0
                ):
                    heading_diff = abs(evt.heading - prev_evt.heading) % 360.0
                    if heading_diff > 180.0:
                        heading_diff = 360.0 - heading_diff

                    if heading_diff >= 140.0:
                        score = min(95.0, 60.0 + (heading_diff * 0.2))
                        reason = f"Sudden {heading_diff:.1f}° heading inversion within {time_delta_sec:.1f}s at {evt.speed:.1f} km/h"
                        anomaly = AnomalyEvent(
                            anomaly_id=str(uuid4()),
                            entity_id=entity.entity_id,
                            anomaly_type="heading_flip",
                            anomaly_score=round(score, 1),
                            reason=reason,
                            detected_at=evt_time,
                        )
                        session.add(anomaly)
                        detected_results.append(
                            DetectedAnomalyResult(
                                anomaly_id=anomaly.anomaly_id,
                                entity_id=entity.entity_id,
                                external_id=entity.external_id,
                                anomaly_type=anomaly.anomaly_type,
                                anomaly_score=anomaly.anomaly_score,
                                reason=anomaly.reason,
                                detected_at=anomaly.detected_at,
                            )
                        )

            # 3. Route corridor deviation check
            for route in routes:
                dev_meters = _calculate_corridor_deviation_meters(
                    evt.latitude,
                    evt.longitude,
                    route.start_latitude,
                    route.start_longitude,
                    route.end_latitude,
                    route.end_longitude,
                )

                if dev_meters > route.max_deviation_meters:
                    excess_dev = dev_meters - route.max_deviation_meters
                    score = min(98.0, 65.0 + (excess_dev * 0.1))
                    reason = f"Off-corridor deviation of {dev_meters:.1f}m on route '{route.route_name}' (max allowed: {route.max_deviation_meters:.0f}m)"
                    anomaly = AnomalyEvent(
                        anomaly_id=str(uuid4()),
                        entity_id=entity.entity_id,
                        route_id=route.route_id,
                        anomaly_type="route_deviation",
                        anomaly_score=round(score, 1),
                        reason=reason,
                        detected_at=evt_time,
                    )
                    session.add(anomaly)
                    detected_results.append(
                        DetectedAnomalyResult(
                            anomaly_id=anomaly.anomaly_id,
                            entity_id=entity.entity_id,
                            external_id=entity.external_id,
                            anomaly_type=anomaly.anomaly_type,
                            anomaly_score=anomaly.anomaly_score,
                            reason=anomaly.reason,
                            detected_at=anomaly.detected_at,
                        )
                    )

    await session.commit()
    return detected_results


def _calculate_corridor_deviation_meters(
    lat: float, lon: float, start_lat: float, start_lon: float, end_lat: float, end_lon: float
) -> float:
    R = 6371000.0
    x = math.radians(lon - start_lon) * math.cos(math.radians((lat + start_lat) / 2.0))
    y = math.radians(lat - start_lat)
    d_start = R * math.sqrt(x * x + y * y)

    x_end = math.radians(end_lon - start_lon) * math.cos(math.radians((end_lat + start_lat) / 2.0))
    y_end = math.radians(end_lat - start_lat)
    d_segment = R * math.sqrt(x_end * x_end + y_end * y_end)

    if d_segment < 1e-6:
        return d_start

    t = max(0.0, min(1.0, (x * x_end + y * y_end) / (d_segment * d_segment / (R * R))))
    proj_x = t * x_end
    proj_y = t * y_end

    dx = x - proj_x
    dy = y - proj_y
    return R * math.sqrt(dx * dx + dy * dy)
