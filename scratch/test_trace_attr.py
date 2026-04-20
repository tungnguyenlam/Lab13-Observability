from langfuse import Langfuse
import os
from dotenv import load_dotenv

load_dotenv()

try:
    langfuse = Langfuse()
    trace = langfuse.trace(name="manual-trace-test")
    print("Successfully called langfuse.trace()")
except AttributeError:
    print("AttributeError: langfuse.trace() really is missing")
except Exception as e:
    print(f"Error: {e}")
