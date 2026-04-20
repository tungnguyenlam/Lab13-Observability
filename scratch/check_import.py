import traceback
try:
    from langfuse import Langfuse
    print("Import successful")
except Exception:
    traceback.print_exc()
