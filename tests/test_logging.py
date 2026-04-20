import json
from pathlib import Path

import structlog

from app.logging_config import configure_logging, scrub_event


def test_scrub_event_redacts_top_level_string_fields() -> None:
    event = {
        "event": "user typed user@example.com",
        "service": "api",
        "correlation_id": "req-abc123",
        "detail": "card 4111 1111 1111 1111 failed",
        "payload": {"message": "call +84 90 123 4567"},
    }
    out = scrub_event(None, "info", event)
    assert "[REDACTED_EMAIL]" in out["event"]
    assert "[REDACTED_CREDIT_CARD]" in out["detail"]
    assert "[REDACTED_PHONE_VN]" in out["payload"]["message"]
    # Safe structural fields must be preserved verbatim.
    assert out["correlation_id"] == "req-abc123"
    assert out["service"] == "api"


def test_configure_logging_writes_scrubbed_jsonl(tmp_path, monkeypatch) -> None:
    log_file = tmp_path / "logs.jsonl"
    monkeypatch.setenv("LOG_PATH", str(log_file))

    # Re-import module to pick up the new LOG_PATH env var.
    import importlib

    from app import logging_config

    importlib.reload(logging_config)
    logging_config.configure_logging()

    log = structlog.get_logger()
    log.info(
        "request_received",
        service="api",
        correlation_id="req-xyz",
        payload={"message": "email student@vinuni.edu.vn"},
    )

    assert log_file.exists(), "JSONL log file was not created"
    lines = [ln for ln in log_file.read_text(encoding="utf-8").splitlines() if ln.strip()]
    assert lines, "no log lines written"
    record = json.loads(lines[-1])
    assert record["correlation_id"] == "req-xyz"
    assert "student@" not in json.dumps(record)
    assert "[REDACTED_EMAIL]" in record["payload"]["message"]
