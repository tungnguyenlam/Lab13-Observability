import os
from dotenv import load_dotenv
from langfuse import Langfuse
from langfuse.decorators import observe, langfuse_context

load_dotenv()

public_key = os.getenv("LANGFUSE_PUBLIC_KEY")
secret_key = os.getenv("LANGFUSE_SECRET_KEY")
host = os.getenv("LANGFUSE_HOST")

print(f"--- Debug Info ---")
print(f"Public Key: {public_key}")
print(f"Secret Key: {secret_key[:10]}...")
print(f"Host: {host}")

if not public_key or not secret_key:
    print("Error: Missing API keys in environment.")
else:
    try:
        # In v4, initialization uses keyword arguments
        langfuse = Langfuse(
            public_key=public_key,
            secret_key=secret_key,
            host=host
        )
        
        # Verify connectivity
        print("Checking connection...")
        if langfuse.auth_check():
            print("Successfully authenticated with Langfuse!")
        else:
            print("Authentication failed (auth_check returned False).")

        # Test tracing via decorators (recommended way in v4)
        @observe()
        def debug_test():
            langfuse_context.update_current_trace(name="debug-test")
            print("Successfully created a test trace via @observe decorator.")

        debug_test()
        
        langfuse.flush()
        print("Flushed traces.")
        print("Check your Langfuse dashboard for a trace named 'debug-test'.")
        
    except Exception as e:
        print(f"Error connecting to Langfuse: {e}")
        import traceback
        traceback.print_exc()
