# Alert Rules and Runbooks

This file is the runbook target referenced by `config/alert_rules.yaml`. The lab app exposes these signals through `/metrics`:

- `latency_p50`, `latency_p95`, `latency_p99`
- `traffic`
- `error_breakdown`
- `avg_cost_usd`, `total_cost_usd`
- `tokens_in_total`, `tokens_out_total`
- `quality_avg`

Recommended operating assumptions for this repo:

- Healthy baseline latency is roughly 150-300ms per request.
- `rag_slow` adds about 2.5s in retrieval and should push P95 above 1.2s almost immediately.
- `tool_fail` creates 500 responses from the retrieval layer and should show up as `RuntimeError`.
- `cost_spike` multiplies output tokens by 4 and should be visible in both cost and tokens-out charts.
- For a school-policy assistant, the biggest product risk is not only downtime but also answering school rules incorrectly or without grounding in the right document.
- Sensitive data risk matters because user prompts may contain student email, phone number, student ID, payment info, or disciplinary details.

## 1. High latency P95
- Severity: P2
- Trigger: `latency_p95_ms > 1200 for 10m`
- Impact: tail latency breaches the latency SLO and users feel the app is slow even if median latency looks normal.
- Main signal:
  `latency_p95` or `latency_p99` climbs while traffic remains stable.
- First checks:
  1. Open slow traces from the last 10-15 minutes in Langfuse.
  2. Compare retrieval time versus LLM generation time inside the waterfall.
  3. Check whether the `rag_slow` incident toggle is currently enabled.
  4. Confirm whether only one feature is affected or every feature is slow.
- Likely root cause in this lab:
  `app/mock_rag.py` is sleeping for 2.5 seconds because `rag_slow` is enabled.
- Mitigation:
  - Disable `rag_slow` if this is an injected incident: `python scripts/inject_incident.py --scenario rag_slow --disable`
  - Reduce retrieval fanout or move to a fallback knowledge source.
  - Trim prompt/context if the LLM span is the real bottleneck.
- Evidence to capture:
  - one slow trace waterfall
  - dashboard panel showing P95/P99 crossing threshold

## 2. High error rate
- Severity: P1
- Trigger: `error_rate_pct > 2 for 5m`
- Impact: users receive failed responses and demo traffic may stop generating useful traces or quality data.
- Main signal:
  5xx responses increase and `error_breakdown` becomes non-empty.
- First checks:
  1. Group logs by `error_type`.
  2. Inspect recent failed traces and note where the exception occurs.
  3. Confirm whether the `tool_fail` incident toggle is enabled.
  4. Compare failure rate by feature to see whether the blast radius is limited.
- Likely root cause in this lab:
  `app/mock_rag.py` raises `RuntimeError("Vector store timeout")` when `tool_fail` is enabled.
- Mitigation:
  - Disable `tool_fail` if this is the planned incident.
  - Retry with a fallback retrieval path or bypass retrieval for low-risk prompts.
  - If the error is not part of the drill, inspect the last code change touching retrieval or request parsing.
- Evidence to capture:
  - one failed trace
  - one structured log line showing `error_type`

## 3. Cost budget spike
- Severity: P2
- Trigger: `avg_cost_usd > 0.004 for 10m`
- Impact: token burn increases faster than expected and the team can no longer explain cost behavior.
- Main signal:
  `avg_cost_usd` rises together with `tokens_out_total`, even if traffic is flat.
- First checks:
  1. Compare `tokens_in_total` versus `tokens_out_total`.
  2. Split traces by feature and model if your dashboard supports it.
  3. Check whether the `cost_spike` incident toggle is enabled.
  4. Verify whether a recent prompt/template change increased output length.
- Likely root cause in this lab:
  `app/mock_llm.py` multiplies output tokens by 4 when `cost_spike` is enabled.
- Mitigation:
  - Disable the incident toggle if this is part of the drill.
  - Shorten prompts and cap output length.
  - Route simple requests to a cheaper model tier.
- Evidence to capture:
  - cost panel before/after incident
  - tokens in/out panel showing output-token jump

## 4. Policy grounding drop
- Severity: P3
- Trigger: `quality_score_avg < 0.85 for 15m`
- Impact: the system may still be up, but answers about school regulations, announcements, or policies are becoming less grounded and less trustworthy.
- Main signal:
  `quality_avg` trends downward while latency and error rate may still look healthy.
- First checks:
  1. Sample a few recent responses and compare them with the original policy question.
  2. Check whether retrieval returned a relevant school-policy document.
  3. Review traces or logs for fallback-style answers that are generic and not policy-specific.
  4. Confirm whether the answer mixes up different categories such as tuition, discipline, attendance, or announcements.
- Likely root cause in this lab:
  retrieval misses, weak answer generation, or repeated fallback responses.
- Mitigation:
  - Improve retrieval keywords and coverage for school regulations, notices, and policy documents.
  - Tighten prompt instructions so answers stay concise and grounded in available documents.
  - Add better quality heuristics if the signal is too noisy.
- Evidence to capture:
  - quality panel with threshold line
  - one response example showing a generic or weakly grounded policy answer

## 5. Knowledge miss for policy questions
- Severity: P2
- Trigger: `repeated fallback answers or missing policy context for 10m`
- Impact: the assistant keeps responding, but cannot reliably answer questions about school rules, which is a product-level incident for this use case.
- Main signal:
  repeated generic answers, low retrieval relevance, or traces showing missing useful context even though policy questions are being asked.
- First checks:
  1. Sample recent questions about regulations, notices, scholarship rules, tuition, attendance, or exam policy.
  2. Check whether retrieval returned any school-specific document or only fallback text.
  3. Identify whether the miss happens only for one topic area or across multiple policy categories.
  4. Confirm whether the underlying corpus lacks the needed document or the retrieval keywords are too weak.
- Likely root cause in this lab:
  the retrieval corpus does not contain the needed school-policy document, or the query does not match the available keywords.
- Mitigation:
  - Add missing policy or announcement documents into the knowledge base.
  - Improve document chunk titles and retrieval keywords for school terminology.
  - Add a safe fallback that explicitly says the bot could not find the relevant rule instead of guessing.
- Evidence to capture:
  - one trace showing weak or missing retrieval context
  - one user-facing answer that should have been policy-grounded but was generic

## 6. PII or student data risk
- Severity: P1
- Trigger: `raw student identifiers appear in logs or responses`
- Impact: potential leakage of sensitive student data such as email, phone number, student ID, payment information, or disciplinary information.
- Main signal:
  logs or responses contain raw personal data instead of hashed or redacted values.
- First checks:
  1. Search logs for raw email addresses, phone numbers, student IDs, or payment-like strings.
  2. Verify that `user_id` is hashed and message previews are redacted.
  3. Inspect whether a response echoed sensitive user input back to the user.
  4. Confirm whether the issue is only in logs, only in responses, or both.
- Likely root cause in this lab:
  incomplete PII redaction, raw input being logged, or prompt/response summarization leaking user data.
- Mitigation:
  - Stop logging the unsafe field immediately or redact it before persistence.
  - Review `app/pii.py` and `app/logging_config.py` for missing masking rules.
  - Re-test with prompts containing school email, phone number, and payment-like strings.
- Evidence to capture:
  - one safe redacted log line
  - if an issue occurs, one sanitized screenshot proving the leak was detected and fixed

## 7. Traffic gap
- Severity: P3
- Trigger: `traffic < 10 requests in 5m during demo window`
- Impact: dashboards may look empty, making it hard to validate SLOs, alerts, and traces live.
- Main signal:
  traffic panel is flat or near zero while the app is otherwise healthy.
- First checks:
  1. Confirm the app is running and `/health` returns `ok`.
  2. Run `python scripts/load_test.py --concurrency 5`.
  3. Verify that the dashboard time window includes the latest requests.
- Likely root cause in this lab:
  load generation was not run, the wrong server address is in use, or the dashboard time range is off.
- Mitigation:
  - Re-run the load test to generate fresh data.
  - Check whether the app is listening on `127.0.0.1:8000`.
  - Refresh the dashboard time filter to the last 15-60 minutes.

## Suggested demo sequence

1. Start from a healthy baseline and capture one screenshot of all panels.
2. Enable `rag_slow`, run `python scripts/load_test.py --concurrency 5`, and show P95 rising.
3. Disable `rag_slow`, enable `tool_fail`, and show error-rate plus `error_breakdown`.
4. Disable `tool_fail`, enable `cost_spike`, and show cost/tokens-out increasing.
5. Show one grounded policy answer and one redacted log example to prove correctness and data safety.
6. Reset incidents and capture a recovery screenshot for the report.
