from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.dependencies import get_db
from app.db.models import Entity
from app.geofence.service import point_in_circle, point_in_polygon

router = APIRouter(tags=["spatial"])


class GeofenceValidateRequest(BaseModel):
    latitude: float
    longitude: float
    geofence_type: str = Field(default="circle", description="'circle' or 'polygon'")
    center_latitude: float | None = None
    center_longitude: float | None = None
    radius_meters: float | None = 1000.0
    polygon: list[tuple[float, float]] | None = None


@router.get("/entities/spatial/bbox")
async def get_entities_spatial_bbox(
    min_lat: float = Query(..., ge=-90.0, le=90.0),
    min_lon: float = Query(..., ge=-180.0, le=180.0),
    max_lat: float = Query(..., ge=-90.0, le=90.0),
    max_lon: float = Query(..., ge=-180.0, le=180.0),
    db: AsyncSession = Depends(get_db),
) -> dict[str, Any]:
    query = (
        select(Entity)
        .where(
            Entity.last_latitude >= min_lat,
            Entity.last_latitude <= max_lat,
            Entity.last_longitude >= min_lon,
            Entity.last_longitude <= max_lon,
        )
        .order_by(Entity.last_seen_at.desc())
    )

    res = await db.execute(query)
    entities = res.scalars().all()

    return {
        "bbox": {"min_lat": min_lat, "min_lon": min_lon, "max_lat": max_lat, "max_lon": max_lon},
        "count": len(entities),
        "entities": [
            {
                "entity_id": e.entity_id,
                "external_id": e.external_id,
                "type": e.type,
                "status": e.status,
                "latitude": e.last_latitude,
                "longitude": e.last_longitude,
                "speed": e.last_speed,
                "last_seen_at": e.last_seen_at.isoformat(),
            }
            for e in entities
        ],
    }


@router.get("/entities/spatial/radius")
async def get_entities_spatial_radius(
    lat: float = Query(..., ge=-90.0, le=90.0),
    lon: float = Query(..., ge=-180.0, le=180.0),
    radius_km: float = Query(default=10.0, gt=0.0, le=500.0),
    db: AsyncSession = Depends(get_db),
) -> dict[str, Any]:
    query = select(Entity)
    res = await db.execute(query)
    all_entities = res.scalars().all()

    radius_meters = radius_km * 1000.0
    matching: list[dict[str, Any]] = []

    for e in all_entities:
        circle_res = point_in_circle(e.last_latitude, e.last_longitude, lat, lon, radius_meters)
        if circle_res.inside:
            matching.append(
                {
                    "entity_id": e.entity_id,
                    "external_id": e.external_id,
                    "type": e.type,
                    "status": e.status,
                    "latitude": e.last_latitude,
                    "longitude": e.last_longitude,
                    "speed": e.last_speed,
                    "distance_meters": circle_res.distance_from_center_meters,
                    "last_seen_at": e.last_seen_at.isoformat(),
                }
            )

    matching.sort(key=lambda item: item["distance_meters"] or 0)

    return {
        "search_point": {"latitude": lat, "longitude": lon, "radius_km": radius_km},
        "count": len(matching),
        "entities": matching,
    }


@router.post("/geofences/validate")
async def validate_geofence_breach(payload: GeofenceValidateRequest) -> dict[str, Any]:
    if payload.geofence_type == "circle":
        if payload.center_latitude is None or payload.center_longitude is None:
            return {"error": "center_latitude and center_longitude required for circle geofence"}

        res = point_in_circle(
            lat=payload.latitude,
            lon=payload.longitude,
            center_lat=payload.center_latitude,
            center_lon=payload.center_longitude,
            radius_meters=payload.radius_meters or 1000.0,
        )
        return {
            "geofence_type": "circle",
            "inside": res.inside,
            "distance_meters": res.distance_from_center_meters,
        }

    elif payload.geofence_type == "polygon":
        if not payload.polygon or len(payload.polygon) < 3:
            return {"error": "at least 3 (lat, lon) vertices required for polygon geofence"}

        inside = point_in_polygon(payload.latitude, payload.longitude, payload.polygon)
        return {
            "geofence_type": "polygon",
            "inside": inside,
            "vertices_count": len(payload.polygon),
        }

    return {"error": "unsupported geofence_type"}
