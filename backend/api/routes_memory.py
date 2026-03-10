"""
api/routes_memory.py
POST /remember  — Store a personal memory or fact.

Authentication: Firebase JWT required.
"""

from fastapi import APIRouter, Depends
from pydantic import BaseModel, Field

from auth.firebase_auth import get_user_id
from memory.memory_store import store_memory
from utils.validators import validate_memory_text
from utils.logger import get_logger

router = APIRouter(prefix="/remember", tags=["Memory"])
logger = get_logger(__name__)


class MemoryRequest(BaseModel):
    text: str = Field(
        ...,
        min_length=3,
        max_length=5000,
        example="The catering vendor is ABC Foods. Contact is Sarah at 555-0101.",
    )


class MemoryResponse(BaseModel):
    stored:  bool
    content: str
    message: str


@router.post("", response_model=MemoryResponse, summary="Store a memory")
async def remember(
    req: MemoryRequest,
    user_id: str = Depends(get_user_id),
):
    """
    Store a personal memory or fact that will be retrievable in future queries.

    The memory is:
      1. Validated
      2. Embedded using nomic-embed-text
      3. Stored in the user's FAISS index (source_type="memory")
      4. Recorded in SQLite for persistence
    """
    text = validate_memory_text(req.text)
    result = store_memory(user_id=user_id, content=text)

    logger.info(f"[{user_id}] Memory stored: '{text[:60]}'")

    return MemoryResponse(
        stored  = True,
        content = result["content"],
        message = "Memory stored successfully. It will be used in future queries.",
    )
