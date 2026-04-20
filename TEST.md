# Logging + PII Verification

Commands to verify Member A's (logging + PII) implementation end-to-end.

## Prerequisites

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
pip install pytest
```

## 1. Unit tests (PII scrubbing)

```bash
source .venv/bin/activate
PYTHONPATH=. pytest tests/test_pii.py -q
```

Expected: `1 passed`.

## 2. End-to-end verification

Run in one shell:

```bash
source .venv/bin/activate
rm -f data/logs.jsonl
uvicorn app.main:app --host 127.0.0.1 --port 8000 --log-level warning &
UVICORN_PID=$!
sleep 2

python scripts/load_test.py --concurrency 5
python scripts/validate_logs.py

kill $UVICORN_PID
```

## Expected output

`load_test.py` prints 10 lines like:

```
[200] req-0b297f96 | qa | 763.1ms
[200] req-1d126b0f | summary | 762.7ms
...
```

Each correlation ID must match `req-<8 hex chars>` (not `MISSING`).

`validate_logs.py` must print:

```
--- Lab Verification Results ---
Total log records analyzed: 21
Records with missing required fields: 0
Records with missing enrichment (context): 0
Unique correlation IDs found: 10
Potential PII leaks detected: 0

--- Grading Scorecard (Estimates) ---
+ [PASSED] Basic JSON schema
+ [PASSED] Correlation ID propagation
+ [PASSED] Log enrichment
+ [PASSED] PII scrubbing

Estimated Score: 100/100
```

## 3. Spot-check PII redaction in the log file

```bash
source .venv/bin/activate
python -c "import json; [print(json.dumps(json.loads(l), indent=2)) for l in open('data/logs.jsonl') if 'refund' in l or '4111' in l or 'phone' in l]"
```

Each matching record must:

- have `correlation_id` set to `req-<8 hex chars>`
- include `user_id_hash`, `session_id`, `feature`, `model`, `env`
- contain `[REDACTED_EMAIL]`, `[REDACTED_PHONE_VN]`, or `[REDACTED_CREDIT_CARD]` inside `payload.message_preview` (never the raw PII)

## 4. Optional: inspect response headers

```bash
curl -i -X POST http://127.0.0.1:8000/chat \
  -H 'content-type: application/json' \
  -d '{"user_id":"u01","session_id":"s01","feature":"qa","message":"hello"}'
```

Response headers must include:

- `x-request-id: req-<8 hex chars>`
- `x-response-time-ms: <integer>`
