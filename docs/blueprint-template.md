# Day 13 Observability Lab Report

> **Instruction**: Fill in all sections below. This report is designed to be parsed by an automated grading assistant. Ensure all tags (e.g., `[GROUP_NAME]`) are preserved.

## 1. Team Metadata
- [GROUP_NAME]: 
- [REPO_URL]: 
- [MEMBERS]:
  - Member A: [Name] | Role: Logging & PII
  - Member B: [Name] | Role: Tracing & Enrichment
  - Member C: [Name] | Role: SLO & Alerts
  - Member D: [Name] | Role: Load Test & Dashboard
  - Member E: [Name] | Role: Demo & Report

---

## 2. Group Performance (Auto-Verified)
- [VALIDATE_LOGS_FINAL_SCORE]: /100
- [TOTAL_TRACES_COUNT]: 
- [PII_LEAKS_FOUND]: 

---

## 3. Technical Evidence (Group)

### 3.1 Logging & Tracing
- [EVIDENCE_CORRELATION_ID_SCREENSHOT]: [Path to image]
- [EVIDENCE_PII_REDACTION_SCREENSHOT]: [Path to image]
- [EVIDENCE_TRACE_WATERFALL_SCREENSHOT]: [Path to image]
- [TRACE_WATERFALL_EXPLANATION]: Trace `agent-run` gồm 2 span con: `retrieve()` (type=retrieval) và `generate()` (type=generation). Khi bật incident `rag_slow`, span `retrieve()` kéo dài từ ~0ms lên ~2500ms trong khi span `generate()` vẫn ~150ms — xác định rõ bottleneck nằm ở tầng RAG chứ không phải LLM.

### 3.2 Dashboard & SLOs
- [DASHBOARD_6_PANELS_SCREENSHOT]: [Path to image]
- [SLO_TABLE]:
| SLI | Target | Window | Current Value |
|---|---:|---|---:|
| Latency P95 | < 3000ms | 28d | |
| Error Rate | < 2% | 28d | |
| Cost Budget | < $2.5/day | 1d | |

### 3.3 Alerts & Runbook
- [ALERT_RULES_SCREENSHOT]: [Path to image]
- [SAMPLE_RUNBOOK_LINK]: [docs/alerts.md#L...]

---

## 4. Incident Response (Group)
- [SCENARIO_NAME]: (e.g., rag_slow)
- [SYMPTOMS_OBSERVED]: 
- [ROOT_CAUSE_PROVED_BY]: (List specific Trace ID or Log Line)
- [FIX_ACTION]: 
- [PREVENTIVE_MEASURE]: 

---

## 5. Individual Contributions & Evidence

### [MEMBER_A_NAME]
- [TASKS_COMPLETED]: 
- [EVIDENCE_LINK]: (Link to specific commit or PR)

### Nguyễn Việt Long — Tracing & Tags
- [TASKS_COMPLETED]:
  1. Xây dựng `_LangfuseContextShim` trong `app/tracing.py` — lớp shim tương thích giúp code gọi `langfuse_context.update_current_trace()` / `update_current_observation()` hoạt động với Langfuse SDK v3/v4 thông qua OTel span attributes (không còn singleton `langfuse_context` trong v3+).
  2. Thêm `@observe()` decorator vào `LabAgent.run()` (`app/agent.py`) để tạo Trace `agent-run` trên Langfuse cho mỗi request.
  3. Thêm `@observe(as_type="retrieval")` vào `retrieve()` (`app/mock_rag.py`) và `@observe(as_type="generation")` vào `FakeLLM.generate()` (`app/mock_llm.py`) để tạo các Observation span con bên trong trace.
  4. Làm giàu trace metadata trong `agent.py`: gắn `name="agent-run"`, `user_id` (hashed), `session_id`, `tags=["lab", feature, model, env]`, và `metadata={"correlation_id": ...}` vào trace; gắn `doc_count`, `query_preview`, `usage_details` vào observation.
  5. Truyền `correlation_id` từ middleware vào `agent.run()` qua `main.py` để liên kết log và trace cùng một request.
  6. Khởi tạo Langfuse singleton tại startup trong `main.py` (`Langfuse()` đọc env vars sau `load_dotenv()`) và log `langfuse_tracing_active` khi tracing bật.
  7. Nâng cấp Langfuse SDK từ `v3.2.1` lên `v4.3.1` (`requirements.txt`) và refactor `_LangfuseContextShim` để dùng `LangfuseOtelSpanAttributes` constants trực tiếp — ổn định hơn và tương thích cả v3 lẫn v4.
- [EVIDENCE_LINK]:
  - Commit `7a69c4e` — "add tracing & tags": https://github.com/tungnguyenlam/Lab13-Observability/commit/7a69c4e
  - Commit `9812882` — "add langfuse" (upgrade v3→v4 & fix shim): https://github.com/tungnguyenlam/Lab13-Observability/commit/9812882
  - PR #5, PR #6: branch `tracing&tags` → `main`

### [Hoang Anh Quyen]
- [TASKS_COMPLETED]: Updated `config/slo.yaml` for the school-policy chatbot use case, added and refined alert rules in `config/alert_rules.yaml`, expanded `docs/alerts.md` with matching runbooks, and adjusted `config/logging_schema.json` to better fit student-policy Q&A logs and compliance needs.
- [EVIDENCE_LINK]: https://github.com/tungnguyenlam/Lab13-Observability/pull/2

### [Nguyen Quang Dang]
- [TASKS_COMPLETED]: Executed concurrent load tests, injected incidents (rag_slow and cost_spike), captured before/after metrics snapshots, and validated recovery after disabling incidents.
- [EVIDENCE_LINK]: docs/evidence/optional/incident-before.png; docs/evidence/optional/incident_after.png; docs/evidence/optional/cost-before-after.png; docs/evidence/optional/auto-instrumentation.png; https://github.com/tungnguyenlam/Lab13-Observability/pull/9.

### [MEMBER_E_NAME]
- [TASKS_COMPLETED]: 
- [EVIDENCE_LINK]: 

---

## 6. Bonus Items (Optional)
- [BONUS_COST_OPTIMIZATION]: (Description + Evidence)
- [BONUS_AUDIT_LOGS]: (Description + Evidence)
- [BONUS_CUSTOM_METRIC]: (Description + Evidence)
