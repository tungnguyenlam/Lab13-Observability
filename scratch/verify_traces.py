"""
verify_traces.py - Queries the Langfuse API to confirm traces were ingested.
Run with: .venv\\Scripts\\python.exe -m scratch.verify_traces
"""
import os
from dotenv import load_dotenv

load_dotenv()

from langfuse import Langfuse

lf = Langfuse()

print("=" * 60)
print("Langfuse Trace Verification")
print("=" * 60)

print(f"\n[OK] Auth check: {lf.auth_check()}")

try:
    traces = lf.api.trace.list(limit=25)
    items = traces.data if hasattr(traces, "data") else []
    print(f"\n[OK] Traces found in Langfuse: {len(items)}")
    print()
    for i, t in enumerate(items[:20], 1):
        name = getattr(t, "name", "?")
        session = getattr(t, "session_id", "?")
        tags = getattr(t, "tags", [])
        user = getattr(t, "user_id", "?")
        print(f"  {i:2}. name={name!r:20s}  user={user!r:20s}  tags={tags}")
    print()
    if len(items) >= 10:
        print("[PASS] >= 10 traces visible in Langfuse")
    else:
        print(f"[FAIL] only {len(items)} trace(s) visible (need >= 10)")
except Exception as e:
    print(f"[ERR] Error fetching traces: {e}")
    print("  (Check the Langfuse dashboard manually.)")

print()
print("Dashboard URL: https://cloud.langfuse.com")

