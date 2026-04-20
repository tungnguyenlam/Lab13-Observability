"""
Smoke test: verifies that the @observe decorator actually pushes a span to Langfuse.
Run with: .venv\Scripts\python.exe scratch/smoke_trace.py
"""
import os
from dotenv import load_dotenv

load_dotenv()

# Initialise the singleton BEFORE importing observe
from langfuse import Langfuse
lf = Langfuse()
print(f"Auth check: {lf.auth_check()}")

import sys
sys.path.insert(0, '.')
from app.tracing import observe, langfuse_context

@observe()
def dummy_rag(query: str) -> list:
    return [f"doc about {query}"]

@observe(as_type="generation")
def dummy_llm(prompt: str) -> str:
    return "This is the answer."

@observe()
def run_pipeline(user_id: str, session_id: str, message: str) -> str:
    docs = dummy_rag(message)
    answer = dummy_llm(f"docs={docs}\nq={message}")

    langfuse_context.update_current_trace(
        name="smoke-test",
        user_id=user_id,
        session_id=session_id,
        tags=["lab", "smoke-test", "dev"],
        metadata={"correlation_id": "smoke-001"},
    )
    langfuse_context.update_current_observation(
        metadata={"doc_count": len(docs), "query_preview": message[:50]},
        usage_details={"input": 40, "output": 20},
    )
    return answer

result = run_pipeline("user-1", "sess-1", "Tell me about refund policy")
print(f"Result: {result}")

print("Flushing traces...")
langfuse_context.flush()
print("Done - check Langfuse dashboard for 'smoke-test' trace.")
