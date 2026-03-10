"""
reasoning/llm_service.py
Calls the OpenAI-compatible LLM API (e.g., Qwen 2.5 via OpenRouter).

Receives context from retrieval + the user query, returns a synthesised
natural-language answer.

Includes retry logic and structured error responses.
"""

import time
import requests
from config.settings import settings
from retrieval.retrieval_service import RetrievalResult
from reasoning.context_builder import build_context_string
from utils.logger import get_logger
from utils.error_handlers import LLMError

logger = get_logger(__name__)

_MAX_RETRIES = 2
_RETRY_DELAY = 2.0  # seconds


def generate_answer(
    query: str,
    retrieval: RetrievalResult,
    extra_instruction: str = "",
    chat_history: list[dict] = None,
) -> str:
    """
    Generate a natural-language answer from retrieved context using the LLM.

    If no context is available, returns a helpful onboarding message instead
    of calling the LLM.

    Args:
        query:             The user's original question.
        retrieval:         RetrievalResult from the retrieval layer.
        extra_instruction: Optional extra instruction appended to the user turn.

    Returns:
        LLM response string or a structured error string on failure.
    """
    if not retrieval.results:
        return (
            "I don't have any indexed data to answer your question yet.\n\n"
            "**To get started:**\n"
            "1. Go to the **Gmail** page and click **Connect with Google**\n"
            "2. Grant read-only access to Gmail, Drive, and Sheets\n"
            "3. Indexing will start automatically — this takes 1–2 minutes\n"
            "4. Come back here and ask your question again\n\n"
            "*Tip: Once indexed, you can ask things like \"What did we decide about the budget?\"*"
        )

    context = build_context_string(retrieval, max_chunks=6)

    user_message = (
        f"Context from your knowledge sources:\n\n"
        f"{context}\n\n"
        f"---\n\n"
        f"Question: {query}\n\n"
        f"CRITICAL REMINDER: You are an AI with a strict rule to NOT hallucinate. You must ONLY use the information present in the Context above. If you cannot find the answer in the Context, strictly output 'I cannot find this information in your documents.'. Do not invent explicit examples, lists, or file names."
    )
    if extra_instruction:
        user_message += f"\n\nAdditional instruction: {extra_instruction}"

    url = f"{settings.llm_base_url.rstrip('/')}/chat/completions"
    headers = {
        "Authorization": f"Bearer {settings.llm_api_key}",
        "Content-Type": "application/json",
        "HTTP-Referer": settings.frontend_url,  # Required by OpenRouter
        "X-Title": "Context-Aware Personal Executive",
    }
    messages = [{"role": "system", "content": settings.system_prompt}]
    
    if chat_history:
        for msg in chat_history:
            # Only add user and assistant messages to prevent invalid roles
            if msg.get("role") in ["user", "assistant"]:
                messages.append({"role": msg["role"], "content": msg.get("content", "")})

    messages.append({"role": "user", "content": user_message})

    payload = {
        "model": settings.llm_model,
        "messages": messages,
        "max_tokens": settings.llm_max_tokens,
        "temperature": settings.llm_temperature,
    }

    last_error = None
    for attempt in range(1, _MAX_RETRIES + 1):
        try:
            logger.info(
                f"LLM request | model={settings.llm_model} | "
                f"attempt={attempt}/{_MAX_RETRIES}"
            )
            response = requests.post(url, headers=headers, json=payload, timeout=90)

            # Handle authentication error explicitly
            if response.status_code == 401:
                logger.error(
                    f"LLM API 401 Unauthorized. "
                    f"Check LLM_API_KEY in .env. "
                    f"Response: {response.text[:200]}"
                )
                return (
                    "⚠️ **LLM API authentication failed** (401 Unauthorized).\n\n"
                    "Please check that `LLM_API_KEY` is correctly set in your `.env` file."
                )

            # Handle rate limiting
            if response.status_code == 429:
                wait = _RETRY_DELAY * attempt
                logger.warning(f"LLM API rate limit hit. Retrying in {wait}s...")
                time.sleep(wait)
                continue

            response.raise_for_status()
            data = response.json()

            # Validate response structure
            choices = data.get("choices", [])
            if not choices:
                logger.error(f"LLM returned empty choices. Response: {data}")
                return "I received an empty response from the AI service. Please try again."

            answer = choices[0].get("message", {}).get("content", "").strip()
            if not answer:
                return "I received an empty response from the AI service. Please try again."

            logger.info(f"LLM answer generated ({len(answer)} chars).")
            return answer

        except requests.exceptions.Timeout:
            last_error = "LLM API request timed out"
            logger.warning(f"[Attempt {attempt}] {last_error}")
            if attempt < _MAX_RETRIES:
                time.sleep(_RETRY_DELAY)

        except requests.exceptions.ConnectionError as exc:
            last_error = f"LLM API connection error: {exc}"
            logger.error(last_error)
            break  # No point retrying a connection error

        except Exception as exc:
            last_error = str(exc)
            logger.error(f"[Attempt {attempt}] LLM API failure: {exc}")
            if attempt < _MAX_RETRIES:
                time.sleep(_RETRY_DELAY)

    logger.error(f"LLM failed after {_MAX_RETRIES} attempts. Last error: {last_error}")
    return (
        f"⚠️ I encountered an error communicating with the AI service: {last_error}\n\n"
        "Please check your `LLM_API_KEY` and `LLM_BASE_URL` settings, then try again."
    )
