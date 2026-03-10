"""
api/routes_query.py
POST /ask  — Ask a natural-language question across all data sources.

Authentication: Firebase JWT required.
"""

from fastapi import APIRouter, Depends
from pydantic import BaseModel, Field

from auth.firebase_auth import get_user_id
from retrieval.retrieval_service import retrieve
from reasoning.llm_service import generate_answer
from utils.validators import validate_query
from utils.logger import get_logger

router = APIRouter(prefix="/ask", tags=["Query"])
logger = get_logger(__name__)


class AskRequest(BaseModel):
    query: str = Field(
        ...,
        min_length=3,
        max_length=2000,
        examples=["What did we decide about event logistics?"],
    )
    chat_history: list[dict] = Field(default_factory=list)


class AskResponse(BaseModel):
    answer:     str
    confidence: str           # e.g. "87%"
    sources:    list[str]     # e.g. ["email", "pdf"]
    result_count: int


@router.post("", response_model=AskResponse, summary="Ask a question")
async def ask(
    req: AskRequest,
    user_id: str = Depends(get_user_id),
):
    """
    Ask a natural-language question. The system:

    1. Embeds the query using nomic-embed-text (Ollama).
    2. Routes to relevant tools via semantic similarity.
    3. Retrieves top-k chunks from FAISS.
    4. Sends context + question to the LLM (Qwen 2.5).
    5. Returns the answer, confidence score, and source list.
    """
    query = validate_query(req.query)
    logger.info(f"[{user_id}] /ask: '{query[:80]}'")

    retrieval = retrieve(user_id=user_id, query=query)
    answer    = generate_answer(query=query, retrieval=retrieval, chat_history=req.chat_history)

    return AskResponse(
        answer       = answer,
        confidence   = retrieval.formatted_confidence(),
        sources      = retrieval.sources,
        result_count = len(retrieval.results),
    )
