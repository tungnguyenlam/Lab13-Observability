# Day 13 Observability Lab Report

> **Instruction**: Fill in all sections below. This report is designed to be parsed by an automated grading assistant. Ensure all tags (e.g., `[GROUP_NAME]`) are preserved.

## 1. Team Metadata
- [GROUP_NAME]: ` X-100`
- Link github: https://github.com/tungnguyenlam/Lab13-Observability
- [MEMBERS]:
  - Member A: [Nguyễn Lâm Tùng, Trần Gia Khánh] | Role: Logging & PII
  - Member B: [Nguyễn Việt Long] | Role: Tracing & Tag
  - Member C: [Hoàng Anh Quyền] | Role: SLO & Alerts
  - Member D: [Nguyễn Quang Đăng] | Role: Load Test & Incident Injection
  - Member E: [Tống Tiến Mạnh] | Role: DashBoard
  - Member F: [Hà Huy Hoàng] | Role: Blueprint Report & Evidence
  - Member G: [Nguyễn Minh Hiếu] | Role: Demo Lead & QA

---

## 2. Group Performance (Auto-Verified)
- [VALIDATE_LOGS_FINAL_SCORE]: ` 100/100 `
- [TOTAL_TRACES_COUNT]: ` 11 `
- [PII_LEAKS_FOUND]: ` 0 `

---

## 3. Technical Evidence (Group)

### 3.1 Logging & Tracing
- [EVIDENCE_CORRELATION_ID_SCREENSHOT]: [Path to image]
- [EVIDENCE_PII_REDACTION_SCREENSHOT]: [Path to image]
- [EVIDENCE_TRACE_WATERFALL_SCREENSHOT]: 
  * [../images/tracing_1.png](../images/tracing_1.png)
  * [../images/tracing_2.png](../images/tracing_2.png)

- [TRACE_WATERFALL_EXPLANATION]: Trace `agent-run` gồm 2 span con: `retrieve()` (type=retrieval) và `generate()` (type=generation). Khi bật incident `rag_slow`, span `retrieve()` kéo dài từ ~0ms lên ~2500ms trong khi span `generate()` vẫn ~150ms — xác định rõ bottleneck nằm ở tầng RAG chứ không phải LLM.

### 3.2 Dashboard & SLOs
- [DASHBOARD_6_PANELS_SCREENSHOT]:
  * [../images/dashboard_latency.png](../images/dashboard_latency.png),
  * [../images/dashboard_traffic-error-rate.png](../images/dashboard_traffic-error-rate.png),
  * [../images/dashboard_cost-token.png](../images/dashboard_cost-token.png), 
  * [../images/dashboard_quality-score.png](../images/dashboard_quality-score.png).

- [SLO_TABLE]:

| SLI | Target | Window | Current Value |
|---|---|---|---|
| Latency P95 | < 3000ms | 28d | |
| Error Rate | < 2% | 28d | |
| Cost Budget | < $2.5/day | 1d | |

### 3.3 Alerts & Runbook
- [ALERT_RULES_SCREENSHOT]: 
  * [../images/alerts_rules_1-2.png](../images/alerts_rules_1-2.png)
  * [../images/alerts_rules_3-4.png](../images/alerts_rules_3-4.png)
  * [../images/alerts_rules_5-6.png](../images/alerts_rules_5-6.png)
  * [../images/alerts_rules_7.png](../images/alerts_rules_7.png)

- SAMPLE RUNBOOK LINK: [docs/alerts.md#L...]

---

## 4. Incident Response (Group)
* [SCENARIO_NAME]: ` cost_spike`.

* [SYMPTOMS_OBSERVED]: During load test bursts, token output and cumulative cost increased faster than baseline while service remained available.

* [ROOT_CAUSE_PROVED_BY]: Metrics before/after incident injection showed increases from avg_cost_usd 0.0065 -> 0.0066, total_cost_usd 0.258 -> 0.3286, tokens_out_total 16928 -> 21568. Incident toggle output confirmed cost_spike=true during the run.

* [FIX_ACTION]: Disabled the incident toggle with scripts/inject_incident.py --scenario cost_spike --disable and verified /health returned cost_spike=false.

* [PREVENTIVE_MEASURE]: Add a repeatable game-day checklist (baseline -> inject -> observe -> rollback), keep cost/token dashboard thresholds visible, and require incident-disable verification after each drill.

---

## 5. Individual Contributions & Evidence

### [Nguyễn Lâm Tùng, Trần Gia Khánh]
- [TASKS_COMPLETED]: Triển khai logging JSON có correlation_id xuyên suốt request, bổ sung log enrichment context, áp dụng PII scrubbing/redaction trong pipeline logging, và verify không rò rỉ PII bằng scripts/validate_logs.py cùng test liên quan.
- [EVIDENCE_LINK]: https://github.com/tungnguyenlam/Lab13-Observability/pull/4; https://github.com/tungnguyenlam/Lab13-Observability/pull/1

### [Nguyễn Việt Long]
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
- [EVIDENCE_LINK]: docs/alert.md; config/alert.yaml; config/slo.yaml; https://github.com/tungnguyenlam/Lab13-Observability/pull/2
### [Nguyen Quang Dang]
- [TASKS_COMPLETED]: Executed concurrent load tests, injected incidents (rag_slow and cost_spike), captured before/after metrics snapshots, and validated recovery after disabling incidents.
- [EVIDENCE_LINK]: docs/evidence/optional/incident-before.png; docs/evidence/optional/incident_after.png; docs/evidence/optional/cost-before-after.png; docs/evidence/optional/auto-instrumentation.png; https://github.com/tungnguyenlam/Lab13-Observability/pull/9.

### [Tong Tien Manh]
- [TASKS_COMPLETED]:
  1. Xây dựng Streamlit dashboard (`scripts/dashboard.py`) hiển thị đủ 6 panel bắt buộc theo `docs/dashboard-spec.md`: Latency P50/P95/P99, Traffic, Error rate + breakdown, Cost over time, Tokens in/out, Quality score avg.
  2. Tích hợp SLO threshold lines (đường đứt nét) trên tất cả panel bằng Plotly — giá trị threshold đọc động từ `config/slo.yaml` thay vì hardcode, đảm bảo dashboard tự cập nhật khi SLO thay đổi.
  3. Cài đặt cơ chế lưu lịch sử theo cửa sổ 1 giờ (trim tự động) và auto refresh mỗi 3 giây để đáp ứng yêu cầu spec (`default time range = 1 hour`, `auto refresh 15-30s`).
  4. Xây dựng hệ thống Active Alerts đọc từ `config/alert_rules.yaml`, evaluate 5 rule có thể tự động theo cửa sổ thời gian (sustained for Xm): `high_latency_p95`, `high_error_rate`, `cost_budget_spike`, `policy_grounding_drop`, `traffic_gap`. Hai rule cần kiểm tra log thủ công được hiển thị riêng trong expander.
  5. Tích hợp Langfuse REST API (`GET /api/public/traces`) vào dashboard — hiển thị tổng số traces, bảng 20 traces gần nhất (ID, Name, Latency, Tokens, Cost, Time), và cảnh báo khi chưa đủ 10 traces cho yêu cầu chấm điểm.
  6. Fix YAML syntax lỗi trong `config/slo.yaml` (dấu `:` trong nội dung note gây `ScannerError`) và cập nhật `requirements.txt` với các package mới: `streamlit==1.56.0`, `plotly==6.7.0`, `pyyaml==6.0.3`.
- [EVIDENCE_LINK]: https://github.com/tungnguyenlam/Lab13-Observability/pull/8

### [Ha Huy Hoang]
- [TASKS_COMPLETED]: Chịu trách nhiệm biên tập và hoàn thiện file `docs/blueprint-template.md` theo chuẩn chấm tự động: chuẩn hóa cấu trúc toàn bộ báo cáo, tổng hợp và liên kết lại minh chứng từ các mảng Tracing/SLO/Incident/Dashboard, đối soát số liệu giữa phần mô tả và screenshot, đồng thời rà soát toàn bộ tag bắt buộc để đảm bảo đúng định dạng và không thiếu trường thông tin.
- [EVIDENCE_LINK]: docs/blueprint-template.md; ../images/tracing_1.png; ../images/tracing_2.png; ../images/dashboard_latency.png; ../images/alerts_rules_1-2.png; https://github.com/tungnguyenlam/Lab13-Observability/pull/11

### [Nguyen Minh Hieu]
- [TASKS_COMPLETED]: Thực hiện kiểm tra chất lượng end-to-end bằng `python scripts/validate_logs.py` để theo dõi mức độ hoàn thành của toàn nhóm, đồng thời điều phối phần live demo và chuẩn bị bộ câu hỏi debug theo `docs/mock-debug-qa.md` nhằm đảm bảo buổi demo ổn định, đúng trọng tâm chấm điểm.
- [EVIDENCE_LINK]: [ ../images/validate_logs.png](../images/validate_logs.png); 

---

## 6. Bonus Items (Optional)
- [BONUS_COST_OPTIMIZATION]: (Description + Evidence)
- [BONUS_AUDIT_LOGS]: (Description + Evidence)
- [BONUS_CUSTOM_METRIC]: (Description + Evidence)
