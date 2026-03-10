"""
api/routes_timeline.py
GET /timeline  — Return a chronological timeline of events for a query.

Authentication: Firebase JWT required.
"""

from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel
from typing import List

from auth.firebase_auth import get_user_id
from retrieval.retrieval_service import retrieve
from timeline.timeline_builder import build_timeline, format_timeline_as_text
from reasoning.llm_service import generate_answer
from utils.validators import validate_query
from utils.logger import get_logger

router = APIRouter(prefix="/timeline", tags=["Timeline"])
logger = get_logger(__name__)


class TimelineEvent(BaseModel):
    date:   str
    text:   str
    source: str
    file:   str


class TimelineResponse(BaseModel):
    query:      str
    events:     List[TimelineEvent]
    summary:    str
    confidence: str


@router.get("", response_model=TimelineResponse, summary="Get event timeline")
async def get_timeline(
    query: str = Query(
        ...,
        min_length=3,
        max_length=500,
        examples=["What happened with the event planning?"],
    ),
    user_id: str = Depends(get_user_id),
):
    """
    Retrieve a chronological timeline for a topic.

    The system:
      1. Searches across all sources for the query.
      2. Extracts date references from matching chunks.
      3. Returns events sorted by date.
      4. Generates an LLM summary of the timeline.
    """
    query = validate_query(query)
    logger.info(f"[{user_id}] /timeline: '{query[:80]}'")

    retrieval = retrieve(user_id=user_id, query=query)
    events    = build_timeline(retrieval)
    timeline_text = format_timeline_as_text(events)

    # Generate a narrative summary of the timeline
    summary = generate_answer(
        query=f"Summarise the following timeline of events:\n\n{timeline_text}",
        retrieval=retrieval,
        extra_instruction="Present the events in chronological order as a clear narrative.",
    )

    return TimelineResponse(
        query      = query,
        events     = [TimelineEvent(**e) for e in events],
        summary    = summary,
        confidence = retrieval.formatted_confidence(),
    )
