from __future__ import annotations

import json
import os
from typing import Any, Dict, List, Optional

try:
    from langfuse import observe
    from langfuse._client.get_client import get_client
    from langfuse._client.attributes import (
        LangfuseOtelSpanAttributes,
        create_trace_attributes,
        create_generation_attributes,
        create_span_attributes,
    )
    from opentelemetry import trace as otel_trace_api

    class _LangfuseContextShim:
        """Compatibility shim that mimics the v2 langfuse_context API using v3 OTel spans.

        In Langfuse v3, there is no langfuse_context singleton. Instead, trace/observation
        metadata is set via OTel span attributes. This shim bridges the gap so that
        existing code using langfuse_context.update_current_trace() and
        langfuse_context.update_current_observation() continues to work.
        """

        @staticmethod
        def _get_current_span() -> otel_trace_api.Span:
            return otel_trace_api.get_current_span()

        def update_current_trace(
            self,
            *,
            name: Optional[str] = None,
            user_id: Optional[str] = None,
            session_id: Optional[str] = None,
            version: Optional[str] = None,
            tags: Optional[List[str]] = None,
            metadata: Optional[Dict[str, Any]] = None,
            public: Optional[bool] = None,
            **kwargs: Any,
        ) -> None:
            """Set trace-level attributes on the current OTel span."""
            span = self._get_current_span()
            if not span.is_recording():
                return

            attributes = create_trace_attributes(
                name=name,
                user_id=user_id,
                session_id=session_id,
                version=version,
                tags=tags,
                metadata=metadata,
                public=public,
            )
            span.set_attributes(attributes)

        def update_current_observation(
            self,
            *,
            metadata: Optional[Any] = None,
            usage_details: Optional[Dict[str, int]] = None,
            **kwargs: Any,
        ) -> None:
            """Set observation-level attributes on the current OTel span."""
            span = self._get_current_span()
            if not span.is_recording():
                return

            attrs: Dict[str, Any] = {}

            # Set observation metadata
            if metadata is not None:
                if isinstance(metadata, dict):
                    for key, value in metadata.items():
                        attr_key = f"{LangfuseOtelSpanAttributes.OBSERVATION_METADATA}.{key}"
                        if isinstance(value, (str, int)):
                            attrs[attr_key] = value
                        else:
                            attrs[attr_key] = json.dumps(value)
                else:
                    attrs[LangfuseOtelSpanAttributes.OBSERVATION_METADATA] = json.dumps(metadata)

            # Set usage details
            if usage_details is not None:
                attrs[LangfuseOtelSpanAttributes.OBSERVATION_USAGE_DETAILS] = json.dumps(usage_details)

            if attrs:
                span.set_attributes(attrs)

        def flush(self) -> None:
            """Flush is handled automatically by the OTel exporter in v3."""
            try:
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
