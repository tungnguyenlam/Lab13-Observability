from __future__ import annotations

import json
import os
from typing import Any, Dict, List, Optional

try:
    from langfuse import observe
    from langfuse._client.attributes import LangfuseOtelSpanAttributes
    from opentelemetry import trace as otel_trace_api

    class _LangfuseContextShim:
        """Compatibility shim that mimics the v2 langfuse_context API using v3/v4 OTel spans.

        In Langfuse v3+, there is no langfuse_context singleton. Instead, trace/observation
        metadata is set via OTel span attributes. This shim bridges the gap so that
        existing code using langfuse_context.update_current_trace() and
        langfuse_context.update_current_observation() continues to work.

        Uses LangfuseOtelSpanAttributes constants directly so it is compatible with
        both Langfuse SDK v3 and v4 — the attribute key strings are stable across both.
        """

        @staticmethod
        def _current_span() -> otel_trace_api.Span:
            return otel_trace_api.get_current_span()

        def update_current_trace(
            self,
            *,
            name: Optional[str] = None,
            user_id: Optional[str] = None,
            session_id: Optional[str] = None,
            version: Optional[str] = None,
            tags: Optional[List[str]] = None,
            metadata: Optional[Any] = None,
            public: Optional[bool] = None,
            **_: Any,
        ) -> None:
            """Set trace-level attributes on the active OTel span."""
            span = self._current_span()
            if not span.is_recording():
                return

            attrs: Dict[str, Any] = {}
            if name is not None:
                attrs[LangfuseOtelSpanAttributes.TRACE_NAME] = name
            if user_id is not None:
                attrs[LangfuseOtelSpanAttributes.TRACE_USER_ID] = user_id
            if session_id is not None:
                attrs[LangfuseOtelSpanAttributes.TRACE_SESSION_ID] = session_id
            if tags is not None:
                attrs[LangfuseOtelSpanAttributes.TRACE_TAGS] = tags
            if public is not None:
                attrs[LangfuseOtelSpanAttributes.TRACE_PUBLIC] = public
            if metadata is not None:
                prefix = LangfuseOtelSpanAttributes.TRACE_METADATA
                if isinstance(metadata, dict):
                    for k, v in metadata.items():
                        attrs[f"{prefix}.{k}"] = (
                            v if isinstance(v, (str, int)) else json.dumps(v)
                        )
                else:
                    attrs[prefix] = json.dumps(metadata)

            if attrs:
                span.set_attributes(attrs)

        def update_current_observation(
            self,
            *,
            metadata: Optional[Any] = None,
            usage_details: Optional[Dict[str, int]] = None,
            **_: Any,
        ) -> None:
            """Set observation-level attributes on the active OTel span."""
            span = self._current_span()
            if not span.is_recording():
                return

            attrs: Dict[str, Any] = {}
            if metadata is not None:
                prefix = LangfuseOtelSpanAttributes.OBSERVATION_METADATA
                if isinstance(metadata, dict):
                    for k, v in metadata.items():
                        attrs[f"{prefix}.{k}"] = (
                            v if isinstance(v, (str, int)) else json.dumps(v)
                        )
                else:
                    attrs[prefix] = json.dumps(metadata)
            if usage_details is not None:
                attrs[LangfuseOtelSpanAttributes.OBSERVATION_USAGE_DETAILS] = json.dumps(
                    usage_details
                )

            if attrs:
                span.set_attributes(attrs)

        def flush(self) -> None:
            """Flush is handled automatically by the OTel batch processor in v3/v4."""
            try:
                from langfuse._client.get_client import get_client
                client = get_client()
                if client is not None:
                    client.flush()
            except Exception:
                pass

    langfuse_context = _LangfuseContextShim()

except Exception as e:  # pragma: no cover
    print(f"WARNING: Langfuse import failed, falling back to dummy tracer. Error: {e}")

    def observe(*args: Any, **kwargs: Any):
        def decorator(func):
            return func
        return decorator

    class _DummyContext:
        def update_current_trace(self, **kwargs: Any) -> None:
            return None

        def update_current_observation(self, **kwargs: Any) -> None:
            return None

        def flush(self) -> None:
            return None

    langfuse_context = _DummyContext()


def tracing_enabled() -> bool:
    return bool(os.getenv("LANGFUSE_PUBLIC_KEY") and os.getenv("LANGFUSE_SECRET_KEY"))
