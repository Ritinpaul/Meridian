from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.dependencies import get_db
from app.nl_query.service import generate_operations_summary, process_natural_language_query

router = APIRouter(tags=["nl_query"])


class NLQueryRequest(BaseModel):
    question: str = Field(min_length=3, examples=["Which vehicles exceeded speed limit in last 30 minutes?"])


@router.post("/query/natural-language")
async def natural_language_query_endpoint(
    payload: NLQueryRequest,
    db: AsyncSession = Depends(get_db),
) -> dict[str, Any]:
    res = await process_natural_language_query(session=db, question=payload.question)
    return res


@router.get("/reports/operations-summary")
async def operations_summary_endpoint(
    window_minutes: int = Query(default=60, ge=1, le=1440),
    db: AsyncSession = Depends(get_db),
) -> dict[str, Any]:
    summary = await generate_operations_summary(session=db, input_window_minutes=window_minutes)
    return summary
