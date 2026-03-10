from retrieval.retrieval_service import RetrievalResult
from reasoning.llm_service import generate_answer

# Dummy retrieval with context
dummy_retrieval = RetrievalResult(
    query="What is the budget?",
    results=[
        {"source_type": "gmail", "file_name": "Email", "text": "The budget is $10,000.", "score": 0.1}
    ],
    confidence=90.0,
    sources=["gmail"]
)

try:
    print("Calling LLM...")
    answer = generate_answer("What is the budget?", dummy_retrieval)
    print(f"Answer: {answer}")
except Exception as e:
    import traceback
    traceback.print_exc()
