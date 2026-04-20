# Day 13 Observability Lab Report

> **Instruction**: Fill in all sections below. This report is designed to be parsed by an automated grading assistant. Ensure all tags (e.g., `[GROUP_NAME]`) are preserved.

## 1. Team Metadata
- [GROUP_NAME]: 
- [REPO_URL]: 
- [MEMBERS]:
  - Member A: [Name] | Role: Logging & PII
  - Member B: [Name] | Role: Tracing & Enrichment
  - Member C: [Name] | Role: SLO & Alerts
  - Member D: [Name] | Role: Load Test & Incident Injection
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
- [TRACE_WATERFALL_EXPLANATION]: (Briefly explain one interesting span in your trace)

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
- [SCENARIO_NAME]: cost_spike
- [SYMPTOMS_OBSERVED]: During load test bursts, token output and cumulative cost increased faster than baseline while service remained available.
- [ROOT_CAUSE_PROVED_BY]: Metrics before/after incident injection showed increases from avg_cost_usd 0.0065 -> 0.0066, total_cost_usd 0.258 -> 0.3286, tokens_out_total 16928 -> 21568. Incident toggle output confirmed cost_spike=true during the run.
- [FIX_ACTION]: Disabled the incident toggle with scripts/inject_incident.py --scenario cost_spike --disable and verified /health returned cost_spike=false.
- [PREVENTIVE_MEASURE]: Add a repeatable game-day checklist (baseline -> inject -> observe -> rollback), keep cost/token dashboard thresholds visible, and require incident-disable verification after each drill.

---

## 5. Individual Contributions & Evidence

### [MEMBER_A_NAME]
- [TASKS_COMPLETED]: 
- [EVIDENCE_LINK]: (Link to specific commit or PR)

### [MEMBER_B_NAME]
- [TASKS_COMPLETED]: 
- [EVIDENCE_LINK]: 

### [MEMBER_C_NAME]
- [TASKS_COMPLETED]: 
- [EVIDENCE_LINK]: 

### [MEMBER_D_NAME]
- [TASKS_COMPLETED]: Executed concurrent load tests, injected incidents (rag_slow and cost_spike), captured before/after metrics snapshots, and validated recovery after disabling incidents.
- [EVIDENCE_LINK]: docs/evidence/optional/incident-before.png; docs/evidence/optional/incident_after.png; docs/evidence/optional/cost-before-after.png; docs/evidence/optional/auto-instrumentation.png; add your commit or PR URL here.

### [MEMBER_E_NAME]
- [TASKS_COMPLETED]: 
- [EVIDENCE_LINK]: 

---

## 6. Bonus Items (Optional)
- [BONUS_COST_OPTIMIZATION]: (Description + Evidence)
- [BONUS_AUDIT_LOGS]: (Description + Evidence)
- [BONUS_CUSTOM_METRIC]: (Description + Evidence)
