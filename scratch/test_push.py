import os
from dotenv import load_dotenv
load_dotenv()

from langfuse.decorators import observe, langfuse_context

@observe()
def test_function():
    print("Running test_function")
    langfuse_context.update_current_trace(
        name="test-trace",
        tags=["test-tag"],
        metadata={"test": "data"}
    )
    return "ok"

if __name__ == "__main__":
    print("Starting test...")
    result = test_function()
    print("Result:", result)
    print("Flushing Langfuse...")
    langfuse_context.flush()
    print("Done.")
