from __future__ import annotations

from datetime import UTC, datetime

import pytest
from app.db.models import Entity
from app.nl_query.service import generate_operations_summary, process_natural_language_query


@pytest.mark.asyncio
async def test_natural_language_query_service(async_session) -> None:
    now = datetime.now(UTC)

    # Populate entity data
    e = Entity(
        external_id="VEH-NL-99",
        type="ambulance",
        status="active",
        last_seen_at=now,
        last_latitude=37.7749,
        last_longitude=-122.4194,
        last_speed=95.0,
        last_heading=45.0,
    )
    async_session.add(e)
    await async_session.commit()

    # Query 1: Speeding vehicles
    res1 = await process_natural_language_query(
        session=async_session,
        question="Show me all speeding vehicles exceeding limit",
    )
    assert res1["sql_generated"].startswith("SELECT")
    assert res1["row_count"] >= 1
    assert res1["execution_ms"] >= 0

    # Query 2: Active fleet count
    res2 = await process_natural_language_query(
        session=async_session,
        question="How many total active entities are on map?",
    )
    assert "count" in res2["summary"].lower() or "entities" in res2["summary"].lower()
    assert res2["execution_ms"] >= 0


@pytest.mark.asyncio
async def test_operations_summary_report(async_session) -> None:
    now = datetime.now(UTC)

    e = Entity(
        external_id="VEH-OPS-01",
        type="patrol",
        status="active",
        last_seen_at=now,
        last_latitude=37.7700,
        last_longitude=-122.4100,
        last_speed=55.0,
        last_heading=90.0,
    )
    async_session.add(e)
    await async_session.commit()

    summary = await generate_operations_summary(session=async_session, input_window_minutes=60)
    assert summary["report_title"] == "Geospatial Operations Command Center Summary"
    assert summary["metrics"]["total_entities_tracked"] >= 1
    assert summary["metrics"]["active_entities"] >= 1
    assert summary["analyst_time_savings_pct"] >= 50.0


@pytest.mark.asyncio
async def test_nl_query_read_only_security_guardrail(async_session) -> None:
    with pytest.raises(ValueError, match="Security Violation"):
        await process_natural_language_query(
            session=async_session,
            question="DROP TABLE entities; SELECT * FROM entities",
        )
