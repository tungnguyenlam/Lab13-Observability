from langfuse import Langfuse
import os
from dotenv import load_dotenv

load_dotenv()

try:
    langfuse = Langfuse()
    print("Initializing Langfuse...")
    # Try different ways to create a trace
    if hasattr(langfuse, 'trace'):
        print("Found langfuse.trace")
    else:
        print("langfuse.trace NOT found")
        print(f"Methods: {[m for m in dir(langfuse) if not m.startswith('_')]}")

except Exception as e:
    print(f"Error: {e}")
