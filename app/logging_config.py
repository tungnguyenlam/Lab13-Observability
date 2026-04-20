from __future__ import annotations

import logging
import os
from pathlib import Path
from typing import Any

import structlog
from structlog.contextvars import merge_contextvars

from .pii import scrub_value

LOG_PATH = Path(os.getenv("LOG_PATH", "data/logs.jsonl"))

# Structural fields that are never free text and should not be scrubbed
# (scrubbing them is cheap but wasteful, and would distort correlation IDs).
_SAFE_KEYS: frozenset[str] = frozenset(
    {
        "ts",
        "level",
        "logger",
        "correlation_id",
        "user_id_hash",
        "session_id",
        "service",
        "feature",
        "model",
        "env",
        "latency_ms",
        "tokens_in",
        "tokens_out",
        "cost_usd",
        "tool_name",
    }
)


class JsonlFileProcessor:
    """Write each structlog event as a JSON line to LOG_PATH.

    Returns the event_dict unchanged so subsequent processors (e.g. the
    console JSONRenderer) still run.
    """

    def __call__(self, logger: Any, method_name: str, event_dict: dict[str, Any]) -> dict[str, Any]:
        LOG_PATH.parent.mkdir(parents=True, exist_ok=True)
        rendered = structlog.processors.JSONRenderer()(logger, method_name, dict(event_dict))
        try:
            with LOG_PATH.open("a", encoding="utf-8") as f:
                f.write(rendered + "\n")
        except OSError:
            # Never let logging crash the request path.
            logging.getLogger(__name__).exception("failed_to_write_log_file")
        return event_dict


def scrub_event(_: Any, __: str, event_dict: dict[str, Any]) -> dict[str, Any]:
    """Recursively redact PII from every free-text field in the event.

    Unlike the naive version that only touched ``payload``/``event``, this
    walks nested dicts and lists so PII cannot leak through fields like
    ``detail``, ``error_message``, or arbitrary tool outputs.
    """
    for key, value in list(event_dict.items()):
        if key in _SAFE_KEYS:
            continue
        event_dict[key] = scrub_value(value)
    return event_dict


def configure_logging() -> None:
    logging.basicConfig(
        format="%(message)s",
        level=getattr(logging, os.getenv("LOG_LEVEL", "INFO").upper(), logging.INFO),
    )
    structlog.configure(
        processors=[
            merge_contextvars,
            structlog.processors.add_log_level,
            structlog.processors.TimeStamper(fmt="iso", utc=True, key="ts"),
            scrub_event,
            structlog.processors.StackInfoRenderer(),
            structlog.processors.format_exc_info,
            JsonlFileProcessor(),
            structlog.processors.JSONRenderer(),
        ],
        wrapper_class=structlog.make_filtering_bound_logger(
            getattr(logging, os.getenv("LOG_LEVEL", "INFO").upper(), logging.INFO)
        ),
        cache_logger_on_first_use=True,
    )


def get_logger() -> structlog.typing.FilteringBoundLogger:
    return structlog.get_logger()
