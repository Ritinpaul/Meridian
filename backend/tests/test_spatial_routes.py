from __future__ import annotations

from datetime import UTC, datetime
import pytest

from app.db.models import Entity


@pytest.mark.asyncio
async def test_spatial_bbox_and_radius_search(async_session) -> None:
    now = datetime.now(UTC)

    # Add entity in SF (37.7749, -122.4194)
    sf_entity = Entity(
        external_id="VEH-SF-01",
        type="truck",
        status="active",
        last_seen_at=now,
        last_latitude=37.7749,
        last_longitude=-122.4194,
        last_speed=50.0,
    )
    async_session.add(sf_entity)

    # Add entity in NY (40.7128, -74.0060)
    ny_entity = Entity(
        external_id="VEH-NY-02",
        type="delivery",
        status="active",
        last_seen_at=now,
        last_latitude=40.7128,
        last_longitude=-74.0060,
        last_speed=30.0,
    )
    async_session.add(ny_entity)
    await async_session.commit()

    # Query BBox for SF region
    bbox_query = (
        f"/entities/spatial/bbox?min_lat=37.0&max_lat=38.0&min_lon=-123.0&max_lon=-122.0"
    )
    from fastapi.testclient import TestClient
    from app.main import app

    client = TestClient(app)
    res = client.get(bbox_query)
    assert res.status_code == 200
    data = res.json()
    assert data["count"] == 1
    assert data["entities"][0]["external_id"] == "VEH-SF-01"

    # Query Radius search around SF (10km radius)
    radius_query = "/entities/spatial/radius?lat=37.7749&lon=-122.4194&radius_km=10.0"
    res_radius = client.get(radius_query)
    assert res_radius.status_code == 200
    radius_data = res_radius.json()
    assert radius_data["count"] == 1
    assert radius_data["entities"][0]["external_id"] == "VEH-SF-01"


def test_geofence_validate_endpoint() -> None:
    from fastapi.testclient import TestClient
    from app.main import app

    client = TestClient(app)

    # Circle geofence check
    res_circle = client.post(
        "/geofences/validate",
        json={
            "latitude": 37.7750,
            "longitude": -122.4190,
            "geofence_type": "circle",
            "center_latitude": 37.7749,
            "center_longitude": -122.4194,
            "radius_meters": 1000.0,
        },
    )
    assert res_circle.status_code == 200
    assert res_circle.json()["inside"] is True

    # Polygon geofence check
    polygon_vertices = [
        [37.7700, -122.4200],
        [37.7800, -122.4200],
        [37.7800, -122.4100],
        [37.7700, -122.4100],
    ]
    res_poly = client.post(
        "/geofences/validate",
        json={
            "latitude": 37.7750,
            "longitude": -122.4150,
            "geofence_type": "polygon",
            "polygon": polygon_vertices,
        },
    )
    assert res_poly.status_code == 200
    assert res_poly.json()["inside"] is True
