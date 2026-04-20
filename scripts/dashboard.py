import os
import time
from datetime import datetime, timedelta, timezone
from pathlib import Path

import httpx
import plotly.graph_objects as go
import streamlit as st
import yaml
from dotenv import load_dotenv

load_dotenv(Path(__file__).parent.parent / ".env")

BASE_URL = "http://127.0.0.1:8000"
REFRESH_INTERVAL = 3  # seconds — spec: 15-30s
MAX_HISTORY = 3600 // REFRESH_INTERVAL  # 1 hour of snapshots — spec: default time range = 1 hour
SLO_PATH = Path(__file__).parent.parent / "config" / "slo.yaml"
ALERT_PATH = Path(__file__).parent.parent / "config" / "alert_rules.yaml"

SEVERITY_COLOR = {"P1": "🔴", "P2": "🟠", "P3": "🟡"}

LAYOUT = dict(height=300, margin=dict(t=30, b=30, l=60, r=20),
              legend=dict(orientation="h", y=-0.25), hovermode="x unified")


def load_slo() -> dict:
    raw = yaml.safe_load(SLO_PATH.read_text(encoding="utf-8"))
    slis = raw.get("slis", {})
    return {
        "latency_p95_ms": slis.get("latency_p95_ms", {}).get("objective", 3000),
        "error_rate_pct": slis.get("error_rate_pct", {}).get("objective", 2.0),
        "quality_avg":    slis.get("quality_score_avg", {}).get("objective", 0.75),
        "daily_cost_usd": slis.get("daily_cost_usd", {}).get("objective", 2.5),
    }


def fetch_metrics() -> dict | None:
    try:
        r = httpx.get(f"{BASE_URL}/metrics", timeout=5.0)
        r.raise_for_status()
        return r.json()
    except Exception as e:
        st.error(f"Cannot reach {BASE_URL}/metrics — {e}")
        return None


def compute_error_rate(m: dict) -> float:
    total = m.get("traffic", 0)
    errors = sum(m.get("error_breakdown", {}).values())
    return round((errors / total * 100), 2) if total > 0 else 0.0


def load_alert_rules() -> list[dict]:
    raw = yaml.safe_load(ALERT_PATH.read_text(encoding="utf-8"))
    return raw.get("alerts", [])


def snapshots_for_minutes(history: list, minutes: int) -> list:
    """Return the last N snapshots covering `minutes` of data."""
    n = max(1, (minutes * 60) // REFRESH_INTERVAL)
    return history[-n:]


def evaluate_alerts(history: list, metrics: dict) -> list[dict]:
    """
    Evaluate numeric alert rules against sustained history windows.
    Returns list of firing alerts: {name, severity, message, runbook}.
    Skips evaluation when no traffic yet to avoid false positives.
    """
    firing = []

    # No data yet — skip all metric-based alerts
    if metrics.get("traffic", 0) == 0:
        return firing

    def sustained(snapshots: list, check) -> bool:
        # Require at least 2 snapshots with actual traffic before firing
        active = [s for s in snapshots if s["traffic"] > 0]
        return len(active) >= 2 and all(check(s) for s in active)

    # high_latency_p95: latency_p95_ms > 1200 for 10m
    w = snapshots_for_minutes(history, 10)
    if sustained(w, lambda s: s["latency_p95"] > 1200):
        firing.append({
            "name": "high_latency_p95", "severity": "P2",
            "message": f"P95 latency = {metrics['latency_p95']:.0f} ms > 1200 ms (sustained 10m)",
            "runbook": "docs/alerts.md#1-high-latency-p95",
        })

    # high_error_rate: error_rate_pct > 2 for 5m
    w = snapshots_for_minutes(history, 5)
    if sustained(w, lambda s: s["error_rate"] > 2):
        firing.append({
            "name": "high_error_rate", "severity": "P1",
            "message": f"Error rate = {metrics['error_breakdown']} (sustained 5m)",
            "runbook": "docs/alerts.md#2-high-error-rate",
        })

    # cost_budget_spike: avg_cost_usd > 0.004 for 10m
    avg_cost = metrics.get("avg_cost_usd", 0)
    if avg_cost > 0.004:
        firing.append({
            "name": "cost_budget_spike", "severity": "P2",
            "message": f"Avg cost/request = ${avg_cost:.5f} > $0.004",
            "runbook": "docs/alerts.md#3-cost-budget-spike",
        })

    # policy_grounding_drop: quality_score_avg < 0.85 for 15m
    w = snapshots_for_minutes(history, 15)
    if sustained(w, lambda s: s["quality_avg"] < 0.85):
        firing.append({
            "name": "policy_grounding_drop", "severity": "P3",
            "message": f"Quality avg = {metrics['quality_avg']:.2f} < 0.85 (sustained 15m)",
            "runbook": "docs/alerts.md#4-policy-grounding-drop",
        })

    # traffic_gap: < 10 new requests in last 5m (only after app has warmed up)
    w = snapshots_for_minutes(history, 5)
    if len(w) >= 2 and w[0]["traffic"] > 0:
        traffic_delta = w[-1]["traffic"] - w[0]["traffic"]
        if traffic_delta < 10:
            firing.append({
                "name": "traffic_gap", "severity": "P3",
                "message": f"Only {traffic_delta} new requests in last 5m (expected ≥ 10)",
                "runbook": "docs/alerts.md#7-traffic-gap",
            })

    return firing


def fetch_langfuse_data() -> dict | None:
    """Fetch traces from Langfuse API for the last 1 hour."""
    public_key = os.getenv("LANGFUSE_PUBLIC_KEY", "")
    secret_key = os.getenv("LANGFUSE_SECRET_KEY", "")
    host = os.getenv("LANGFUSE_HOST", "https://cloud.langfuse.com").rstrip("/")
    if not public_key or not secret_key:
        return None
    try:
        from_time = (datetime.now(timezone.utc) - timedelta(hours=1)).strftime("%Y-%m-%dT%H:%M:%SZ")
        r = httpx.get(
            f"{host}/api/public/traces",
            params={"limit": 50, "fromTimestamp": from_time},
            auth=(public_key, secret_key),
            timeout=10.0,
        )
        r.raise_for_status()
        data = r.json()
        traces = data.get("data", [])
        return {
            "total": data.get("meta", {}).get("totalItems", len(traces)),
            "traces": traces,
        }
    except Exception as e:
        return {"error": str(e), "total": 0, "traces": []}


def slo_hline(fig: go.Figure, y: float, label: str, color: str = "red") -> None:
    fig.add_hline(y=y, line_dash="dash", line_color=color,
                  annotation_text=label, annotation_position="top left",
                  annotation_font_color=color)


# ── Bootstrap ─────────────────────────────────────────────────────────────────
SLO = load_slo()
ALERT_RULES = load_alert_rules()
st.set_page_config(page_title="Day 13 Observability Dashboard", layout="wide")
st.title("Day 13 — Observability Dashboard")

if "history" not in st.session_state:
    st.session_state.history = []

metrics = fetch_metrics()
if metrics is None:
    st.stop()

error_rate = compute_error_rate(metrics)

# Append + trim to 1-hour window — spec: default time range = 1 hour
st.session_state.history.append({
    "time":         datetime.now().strftime("%H:%M:%S"),
    "latency_p50":  metrics["latency_p50"],
    "latency_p95":  metrics["latency_p95"],
    "latency_p99":  metrics["latency_p99"],
    "traffic":      metrics["traffic"],
    "error_rate":   error_rate,
    "total_cost":   metrics["total_cost_usd"],
    "tokens_in":    metrics["tokens_in_total"],
    "tokens_out":   metrics["tokens_out_total"],
    "quality_avg":  metrics["quality_avg"],
})
if len(st.session_state.history) > MAX_HISTORY:
    st.session_state.history = st.session_state.history[-MAX_HISTORY:]

history = st.session_state.history
times = [h["time"] for h in history]

st.caption(
    f"Last updated: {times[-1]} | "
    f"Auto refresh: {REFRESH_INTERVAL}s | "
    f"Time window: last 1 hour ({len(history)} snapshots)"
)

# ── KPI cards ─────────────────────────────────────────────────────────────────
c1, c2, c3, c4 = st.columns(4)
c1.metric("Traffic", f"{metrics['traffic']} requests")
c2.metric("Latency P95",  f"{metrics['latency_p95']:.0f} ms",
          delta=f"SLO ≤ {SLO['latency_p95_ms']} ms", delta_color="off")
c3.metric("Error rate",   f"{error_rate:.2f} %",
          delta=f"SLO ≤ {SLO['error_rate_pct']} %", delta_color="off")
c4.metric("Quality avg",  f"{metrics['quality_avg']:.2f}",
          delta=f"SLO ≥ {SLO['quality_avg']}", delta_color="off")

st.divider()

# ── Active Alerts ─────────────────────────────────────────────────────────────
st.subheader("🚨 Active Alerts")
firing = evaluate_alerts(history, metrics)

# Manual-check rules (cannot evaluate from metrics alone)
MANUAL_RULES = [
    {"name": "knowledge_miss_for_policy_questions", "severity": "P2",
     "message": "Manual check required — repeated fallback answers or missing policy context",
     "runbook": "docs/alerts.md#5-knowledge-miss-for-policy-questions"},
    {"name": "pii_or_student_data_risk", "severity": "P1",
     "message": "Manual check required — inspect logs for raw student identifiers",
     "runbook": "docs/alerts.md#6-pii-or-student-data-risk"},
]

if firing:
    for alert in sorted(firing, key=lambda a: a["severity"]):
        icon = SEVERITY_COLOR.get(alert["severity"], "⚪")
        st.error(
            f"{icon} **[{alert['severity']}] {alert['name']}** — {alert['message']}  \n"
            f"Runbook: `{alert['runbook']}`"
        )
else:
    st.success("All automated alert rules OK.")

with st.expander("Manual-check rules (require log inspection)"):
    for rule in MANUAL_RULES:
        icon = SEVERITY_COLOR.get(rule["severity"], "⚪")
        st.warning(
            f"{icon} **[{rule['severity']}] {rule['name']}** — {rule['message']}  \n"
            f"Runbook: `{rule['runbook']}`"
        )

st.divider()

# ── Panel 1: Latency P50 / P95 / P99 ─────────────────────────────────────────
st.subheader("1. Latency P50 / P95 / P99")

fig1 = go.Figure()
fig1.add_trace(go.Scatter(x=times, y=[h["latency_p50"] for h in history],
    mode="lines+markers", name="P50 (ms)", line=dict(color="#2196F3")))
fig1.add_trace(go.Scatter(x=times, y=[h["latency_p95"] for h in history],
    mode="lines+markers", name="P95 (ms)", line=dict(color="#111111")))
fig1.add_trace(go.Scatter(x=times, y=[h["latency_p99"] for h in history],
    mode="lines+markers", name="P99 (ms)", line=dict(color="#F44336")))
slo_hline(fig1, SLO["latency_p95_ms"], f"SLO P95 ≤ {SLO['latency_p95_ms']} ms")
fig1.update_layout(**LAYOUT, xaxis_title="Time", yaxis_title="Latency (ms)")
st.plotly_chart(fig1, use_container_width=True)

if metrics["latency_p95"] > SLO["latency_p95_ms"]:
    st.warning(f"SLO BREACH: P95 = {metrics['latency_p95']:.0f} ms > {SLO['latency_p95_ms']} ms")
else:
    st.success(f"SLO OK: P95 = {metrics['latency_p95']:.0f} ms ≤ {SLO['latency_p95_ms']} ms")

st.divider()

# ── Panel 2 & 3: Traffic + Error rate ────────────────────────────────────────
col2, col3 = st.columns(2)

with col2:
    st.subheader("2. Traffic")
    fig2 = go.Figure()
    fig2.add_trace(go.Scatter(x=times, y=[h["traffic"] for h in history],
        mode="lines+markers", name="Requests (count)", line=dict(color="#4CAF50")))
    fig2.update_layout(**LAYOUT, xaxis_title="Time", yaxis_title="Requests (count)")
    st.plotly_chart(fig2, use_container_width=True)

with col3:
    st.subheader("3. Error rate + breakdown")
    fig3 = go.Figure()
    fig3.add_trace(go.Scatter(x=times, y=[h["error_rate"] for h in history],
        mode="lines+markers", name="Error rate (%)", line=dict(color="#E91E63"),
        fill="tozeroy", fillcolor="rgba(233,30,99,0.1)"))
    slo_hline(fig3, SLO["error_rate_pct"], f"SLO ≤ {SLO['error_rate_pct']} %")
    fig3.update_layout(**LAYOUT, xaxis_title="Time", yaxis_title="Error rate (%)")
    st.plotly_chart(fig3, use_container_width=True)

    breakdown = metrics.get("error_breakdown", {})
    if breakdown:
        for err_type, count in breakdown.items():
            st.caption(f"• `{err_type}`: {count} errors")
        if error_rate > SLO["error_rate_pct"]:
            st.warning(f"SLO BREACH: error rate {error_rate}% > {SLO['error_rate_pct']}%")
    else:
        st.caption("No errors recorded.")

st.divider()

# ── Panel 4 & 5: Cost + Tokens ───────────────────────────────────────────────
col4, col5 = st.columns(2)

with col4:
    st.subheader("4. Cost over time")
    fig4 = go.Figure()
    fig4.add_trace(go.Scatter(x=times, y=[h["total_cost"] for h in history],
        mode="lines+markers", name="Total cost (USD)", line=dict(color="#9C27B0")))
    slo_hline(fig4, SLO["daily_cost_usd"], f"SLO daily ≤ ${SLO['daily_cost_usd']}", color="orange")
    fig4.update_layout(**LAYOUT, xaxis_title="Time", yaxis_title="Cost (USD)")
    st.plotly_chart(fig4, use_container_width=True)
    st.caption(
        f"Total: **${metrics['total_cost_usd']:.4f} USD** | "
        f"Avg/request: **${metrics['avg_cost_usd']:.4f} USD**"
    )

with col5:
    st.subheader("5. Tokens in / out")
    fig5 = go.Figure()
    fig5.add_trace(go.Scatter(x=times, y=[h["tokens_in"] for h in history],
        mode="lines+markers", name="Tokens in", line=dict(color="#00BCD4")))
    fig5.add_trace(go.Scatter(x=times, y=[h["tokens_out"] for h in history],
        mode="lines+markers", name="Tokens out", line=dict(color="#FF5722")))
    fig5.update_layout(**LAYOUT, xaxis_title="Time", yaxis_title="Tokens (count)")
    st.plotly_chart(fig5, use_container_width=True)
    st.caption(
        f"Total in: **{metrics['tokens_in_total']:,} tokens** | "
        f"Total out: **{metrics['tokens_out_total']:,} tokens**"
    )

st.divider()

# ── Panel 6: Quality proxy ────────────────────────────────────────────────────
st.subheader("6. Quality score (avg)")
fig6 = go.Figure()
fig6.add_trace(go.Scatter(x=times, y=[h["quality_avg"] for h in history],
    mode="lines+markers", name="Quality avg (0–1)", line=dict(color="#8BC34A"),
    fill="tozeroy", fillcolor="rgba(139,195,74,0.1)"))
slo_hline(fig6, SLO["quality_avg"], f"SLO ≥ {SLO['quality_avg']}", color="green")
fig6.update_layout(**LAYOUT, xaxis_title="Time", yaxis_title="Quality score (0–1)",
                   yaxis=dict(range=[0, 1]))
st.plotly_chart(fig6, use_container_width=True)

if metrics["quality_avg"] < SLO["quality_avg"]:
    st.warning(f"SLO BREACH: quality {metrics['quality_avg']:.2f} < {SLO['quality_avg']}")
else:
    st.success(f"SLO OK: quality {metrics['quality_avg']:.2f} ≥ {SLO['quality_avg']}")

# ── Langfuse Traces ───────────────────────────────────────────────────────────
st.divider()
st.subheader("Langfuse Traces (last 1 hour)")

lf = fetch_langfuse_data()
if lf is None:
    st.warning("Langfuse keys not set — skipping trace panel.")
elif "error" in lf:
    st.error(f"Langfuse error: {lf['error']}")
else:
    total = lf["total"]
    traces = lf["traces"]
    grading_ok = total >= 10

    col_lf1, col_lf2 = st.columns([1, 3])
    with col_lf1:
        st.metric("Total traces", total,
                  delta="✓ ≥ 10 (grading OK)" if grading_ok else "✗ need ≥ 10",
                  delta_color="normal" if grading_ok else "inverse")
    with col_lf2:
        if not grading_ok:
            st.warning(f"Only {total} traces — need ≥ 10 for grading. Run more requests.")
        else:
            st.success(f"{total} traces found — grading requirement met.")

    if traces:
        rows = []
        for t in traces[:20]:
            latency_ms = None
            if t.get("latency"):
                latency_ms = round(t["latency"] * 1000)
            rows.append({
                "ID":        t.get("id", "")[:8] + "...",
                "Name":      t.get("name", "—"),
                "Latency (ms)": latency_ms,
                "Tokens":    t.get("totalTokens"),
                "Cost (USD)": t.get("totalCost"),
                "Time":      (t.get("timestamp") or "")[:19].replace("T", " "),
            })
        st.dataframe(rows, use_container_width=True, hide_index=True)

# ── Auto refresh ──────────────────────────────────────────────────────────────
time.sleep(REFRESH_INTERVAL)
st.rerun()
