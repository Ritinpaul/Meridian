from __future__ import annotations

from datetime import UTC, datetime
from typing import Any
from uuid import uuid4

from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.anomaly.detector import run_anomaly_detection
from app.api.dependencies import get_db
from app.db.models import AnomalyEvent, RouteDefinition

router = APIRouter(tags=["anomalies"])


class AnomalyDetectRequest(BaseModel):
    window_minutes: int = Field(default=60, ge=1, le=1440)
    entity_id: str | None = None


class RouteDefinitionCreateRequest(BaseModel):
    route_name: str
    start_latitude: float
    start_longitude: float
    end_latitude: float
    end_longitude: float
    max_deviation_meters: float = 200.0
    max_speed_kms: float = 120.0


@router.post("/anomalies/detect")
async def detect_anomalies_endpoint(
    payload: AnomalyDetectRequest,
    db: AsyncSession = Depends(get_db),
) -> dict[str, Any]:
    results = await run_anomaly_detection(
        session=db,
        window_minutes=payload.window_minutes,
        entity_id=payload.entity_id,
    )
    return {
        "status": "success",
        "window_minutes": payload.window_minutes,
        "anomalies_detected_count": len(results),
        "anomalies": [
            {
                "anomaly_id": r.anomaly_id,
                "entity_id": r.entity_id,
                "external_id": r.external_id,
                "anomaly_type": r.anomaly_type,
                "anomaly_score": r.anomaly_score,
                "reason": r.reason,
                "detected_at": r.detected_at.isoformat(),
            }
            for r in results
        ],
    }


@router.get("/anomalies/latest")
async def get_latest_anomalies(
    limit: int = Query(default=50, ge=1, le=500),
    db: AsyncSession = Depends(get_db),
) -> dict[str, Any]:
    query = select(AnomalyEvent).order_by(AnomalyEvent.detected_at.desc()).limit(limit)
    res = await db.execute(query)
    anomalies = res.scalars().all()

    return {
        "count": len(anomalies),
        "anomalies": [
            {
                "anomaly_id": a.anomaly_id,
                "entity_id": a.entity_id,
                "anomaly_type": a.anomaly_type,
                "anomaly_score": a.anomaly_score,
                "reason": a.reason,
                "detected_at": a.detected_at.isoformat(),
            }
            for a in anomalies
        ],
    }


@router.post("/routes/definition")
async def create_route_definition(
    payload: RouteDefinitionCreateRequest,
    db: AsyncSession = Depends(get_db),
) -> dict[str, Any]:
    route = RouteDefinition(
        route_id=str(uuid4()),
        route_name=payload.route_name,
        start_latitude=payload.start_latitude,
        start_longitude=payload.start_longitude,
        end_latitude=payload.end_latitude,
        end_longitude=payload.end_longitude,
        max_deviation_meters=payload.max_deviation_meters,
        max_speed_kms=payload.max_speed_kms,
        created_at=datetime.now(UTC),
    )
    db.add(route)
    await db.commit()

    return {
        "status": "created",
        "route_id": route.route_id,
        "route_name": route.route_name,
        "max_deviation_meters": route.max_deviation_meters,
    }
