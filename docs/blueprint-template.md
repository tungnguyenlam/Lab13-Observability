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
  * [images/tracing_1.png](images/tracing_1.png)
  * [images/tracing_2.png](images/tracing_2.png)

- [TRACE_WATERFALL_EXPLANATION]: (Briefly explain one interesting span in your trace)

### 3.2 Dashboard & SLOs
- [DASHBOARD_6_PANELS_SCREENSHOT]:
  * [images/dashboard_latency.png](images/dashboard_latency.png),
  * [images/dashboard_traffic-error-rate.png](images/dashboard_traffic-error-rate.png),
  * [images/dashboard_cost-token.png](images/dashboard_cost-token.png), 
  * [images/dashboard_quality-score.png](images/dashboard_quality-score.png).

- [SLO_TABLE]:

| SLI | Target | Window | Current Value |
|---|---|---|---|
| Latency P95 | < 3000ms | 28d | |
| Error Rate | < 2% | 28d | |
| Cost Budget | < $2.5/day | 1d | |

### 3.3 Alerts & Runbook
- [ALERT_RULES_SCREENSHOT]: 
  * [images/alerts_rules_1-2.png](images/alerts_rules_1-2.png)
  * [images/alerts_rules_3-4.png](images/alerts_rules_3-4.png)
  * [images/alerts_rules_5-6.png](images/alerts_rules_5-6.png)
  * [images/alerts_rules_7.png](images/alerts_rules_7.png)

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

### [MEMBER_A_NAME]
- [TASKS_COMPLETED]: Triển khai logging JSON có correlation_id xuyên suốt request, bổ sung log enrichment context, áp dụng PII scrubbing/redaction trong pipeline logging, và verify không rò rỉ PII bằng scripts/validate_logs.py cùng test liên quan.
- [EVIDENCE_LINK]: (Link to specific commit or PR)

### [MEMBER_B_NAME]
- [TASKS_COMPLETED]: Đảm bảo decorator @observe hoạt động trong app/agent.py, cấu hình langfuse_context.update_current_trace đúng user_id/session_id/tags, gửi 10-20 request và verify traces trên Langfuse UI.
- [EVIDENCE_LINK]: 

### [MEMBER_C_NAME]
- [TASKS_COMPLETED]: Chỉnh targets trong config/slo.yaml cho phù hợp nhóm, bổ sung/hoàn thiện rules trong config/alert_rules.yaml, và viết runbook trong docs/alerts.md.
- [EVIDENCE_LINK]: 

### [MEMBER_D_NAME]
- [TASKS_COMPLETED]: Chạy python scripts/load_test.py --concurrency 5, chạy python scripts/inject_incident.py --scenario rag_slow, ghi lại triệu chứng và root cause cho phần Incident Response trong báo cáo.
- [EVIDENCE_LINK]: 

### [MEMBER_E_NAME]
- [TASKS_COMPLETED]: Build dashboard 6 panel (Latency P50/P95/P99, Traffic, Error Rate, Cost, Tokens, Quality) theo docs/dashboard-spec.md và chụp screenshot đủ 6 panel.
- [EVIDENCE_LINK]: 

### [MEMBER_F_NAME]
- [TASKS_COMPLETED]: Điền đầy đủ docs/blueprint-template.md, thu thập screenshot/evidence từ B/C/D/E, và đảm bảo tất cả tags [ ... ] trong báo cáo được điền đầy đủ.
- [EVIDENCE_LINK]: 

### [MEMBER_G_NAME]
- [TASKS_COMPLETED]: Chạy python scripts/validate_logs.py để kiểm tra tiến độ toàn nhóm, chuẩn bị live demo, và đặt câu hỏi debug theo docs/mock-debug-qa.md.
- [EVIDENCE_LINK]: 

---

## 6. Bonus Items (Optional)
- [BONUS_COST_OPTIMIZATION]: (Description + Evidence)
- [BONUS_AUDIT_LOGS]: (Description + Evidence)
- [BONUS_CUSTOM_METRIC]: (Description + Evidence)
