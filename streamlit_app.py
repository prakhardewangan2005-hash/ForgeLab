import os
import sys
import json
import time
import glob
import uuid
import subprocess
import pathlib
from statistics import mean

import streamlit as st

APP_TITLE = "ForgeLab-RTP"
APP_SUBTITLE = "System-Level Server Bring-Up, Thermal & Power Validation Platform"

st.set_page_config(page_title=APP_TITLE, layout="wide")

# -----------------------
# Dark purple theme + layout polish
# -----------------------
st.markdown(
    """
    <style>
      :root{
        --bg0: #0b0720;     /* deep purple */
        --bg1: #120a2b;     /* panel */
        --card: rgba(255,255,255,.04);
        --border: rgba(255,255,255,.10);
        --muted: rgba(255,255,255,.72);
        --mono: ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, "Liberation Mono","Courier New", monospace;
      }

      /* page background */
      html, body, [data-testid="stAppViewContainer"], .stApp {
        background: radial-gradient(1200px 900px at 20% 10%, #1a0f40 0%, var(--bg0) 55%) !important;
      }

      /* reduce excessive padding + center width */
      .block-container { padding-top: 2rem; padding-bottom: 2rem; max-width: 1250px; }

      /* cards */
      .card {
        border: 1px solid var(--border);
        border-radius: 16px;
        padding: 14px 16px;
        background: var(--card);
        backdrop-filter: blur(10px);
      }

      .smallcaps { letter-spacing: .08em; text-transform: uppercase; font-size: 0.75rem; opacity: .75; }
      .muted { color: var(--muted); }
      .mono { font-family: var(--mono); }

      /* code blocks and json blocks */
      pre, code { font-family: var(--mono) !important; }
      [data-testid="stCodeBlock"], [data-testid="stJson"] {
        border-radius: 14px !important;
        border: 1px solid var(--border) !important;
        background: rgba(255,255,255,.03) !important;
      }

      /* artifact preview boxes height */
      .artifactBox {
        border: 1px solid var(--border);
        border-radius: 16px;
        padding: 12px 12px;
        background: rgba(255,255,255,.03);
        height: 520px;
        overflow: hidden;
      }
      .artifactScroll {
        height: 420px;
        overflow: auto;
        padding-right: 6px;
      }

      /* pills */
      .pill { display:inline-block; padding:4px 10px; border-radius: 999px; border: 1px solid var(--border); margin-right:6px; margin-bottom:6px; }
      .ok { border-color: rgba(34,197,94,.50); }
      .bad { border-color: rgba(239,68,68,.55); }
      .warn { border-color: rgba(245,158,11,.55); }
    </style>
    """,
    unsafe_allow_html=True,
)

# -----------------------
# Header
# -----------------------
st.markdown("<div class='smallcaps'>Release-to-Production • Validation • Debug</div>", unsafe_allow_html=True)
st.title(APP_TITLE)
st.caption(APP_SUBTITLE)

# Ensure dirs exist
os.makedirs("logs", exist_ok=True)
os.makedirs("reports", exist_ok=True)

# -----------------------
# Helpers
# -----------------------
def latest_artifacts():
    logs = sorted(glob.glob("logs/*.json"), key=os.path.getmtime, reverse=True)
    rmd = sorted(glob.glob("reports/*.md"), key=os.path.getmtime, reverse=True)
    csvs = sorted(glob.glob("reports/*.csv"), key=os.path.getmtime, reverse=True)
    return logs, rmd, csvs

def read_tail(path, max_lines=200):
    try:
        with open(path, "r", encoding="utf-8", errors="ignore") as f:
            lines = f.readlines()
        return "".join(lines[-max_lines:])
    except Exception as e:
        return f"(failed to read {path}: {e})"

def try_parse_json(path):
    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return None

def pick_first_key(dct, keys):
    for k in keys:
        if isinstance(dct, dict) and k in dct:
            return dct[k]
    return None

def extract_overall_status(log_obj):
    """
    Prefer explicit status fields from log/report.
    Falls back to None if not present.
    """
    if not isinstance(log_obj, dict):
        return None
    # common patterns
    for k in ["overall_status", "status", "result", "outcome"]:
        v = log_obj.get(k)
        if isinstance(v, str) and v.strip():
            return v.strip().upper()

    # nested summary
    summary = pick_first_key(log_obj, ["summary", "run_summary", "report"])
    if isinstance(summary, dict):
        for k in ["overall_status", "status", "result", "outcome"]:
            v = summary.get(k)
            if isinstance(v, str) and v.strip():
                return v.strip().upper()

    return None

def normalize_events(obj):
    raw = pick_first_key(obj, ["events", "procedure", "steps", "timeline"])
    if not isinstance(raw, list):
        return []
    out = []
    for i, e in enumerate(raw):
        if isinstance(e, str):
            out.append({"ts": None, "name": e, "status": None, "detail": None})
        elif isinstance(e, dict):
            ts = e.get("ts") or e.get("time") or e.get("timestamp")
            name = e.get("name") or e.get("step") or e.get("event") or f"step_{i+1}"
            status = e.get("status") or e.get("result") or e.get("state")
            detail = e.get("detail") or e.get("msg") or e.get("message") or e.get("notes")
            out.append({"ts": ts, "name": name, "status": status, "detail": detail})
    return out

def normalize_samples(obj):
    raw = pick_first_key(obj, ["samples", "telemetry", "signals", "metrics"])
    if isinstance(raw, list) and raw and isinstance(raw[0], dict):
        return raw
    return []

def series_stats(values):
    if not values:
        return None
    vmin = min(values)
    vmax = max(values)
    vavg = mean(values)
    trend = "↗" if values[-1] > values[0] else ("↘" if values[-1] < values[0] else "→")
    return {"min": vmin, "max": vmax, "avg": vavg, "trend": trend}

def extract_signal_series(samples, possible_keys):
    series = []
    for s in samples:
        if not isinstance(s, dict):
            continue
        val = None
        for k in possible_keys:
            if k in s:
                val = s.get(k)
                break
        if isinstance(val, (int, float)):
            series.append(float(val))
    return series

def infer_failure_modes(obj, samples):
    failures = pick_first_key(obj, ["failures", "failure_modes", "faults", "alerts"])
    if isinstance(failures, list) and failures:
        out = []
        for f in failures:
            if isinstance(f, str):
                out.append(f)
            elif isinstance(f, dict):
                out.append(f.get("name") or f.get("type") or json.dumps(f))
        return out, True

    cpu_temp = extract_signal_series(samples, ["cpu_temp_c", "cpu_temp", "cpu_temperature_c"])
    psu_v = extract_signal_series(samples, ["psu_voltage_v", "psu_voltage", "v_psu"])
    fan_rpm = extract_signal_series(samples, ["fan_rpm", "rpm_fan", "fan0_rpm"])

    inferred = []
    if cpu_temp and max(cpu_temp) >= 90:
        inferred.append("THERMAL_THROTTLE_RISK (CPU temp >= 90C)")
    if psu_v and min(psu_v) <= 10.8:
        inferred.append("PSU_VOLTAGE_SAG (min <= 10.8V)")
    if fan_rpm and min(fan_rpm) <= 400:
        inferred.append("FAN_STALL_OR_LOW_RPM (min <= 400 RPM)")

    events = normalize_events(obj) if isinstance(obj, dict) else []
    bad_steps = [e for e in events if (e.get("status") or "").lower() in ("fail", "failed", "error")]
    if bad_steps:
        inferred.append(f"BRINGUP_STEP_FAILURE ({bad_steps[0].get('name')})")

    return inferred, False

# -----------------------
# Sidebar: run controls
# -----------------------
with st.sidebar:
    st.markdown("### Run Controls")
    PLAN_OPTIONS = {
        "Bring-Up Validation": "testplans/bringup.yaml",
        "Thermal Stress Test": "testplans/thermal.yaml",
        "Power Validation": "testplans/power.yaml",
    }
    plan_name = st.selectbox("Test plan", list(PLAN_OPTIONS.keys()), index=1)
    plan_path = PLAN_OPTIONS[plan_name]

    seed = st.number_input("Deterministic seed", min_value=0, max_value=999999, value=1337, step=1)
    inject = st.toggle("Enable failure injection", value=True)
    verbose = st.toggle("Verbose output", value=False)

    st.markdown("---")
    st.markdown("### Demo mode")
    demo_mode = st.toggle("Make status less harsh (show WARN for non-zero exit unless report says FAIL)", value=True)
    st.caption("Keeps the dashboard from looking broken during simulated failure injection.")

# -----------------------
# Top row
# -----------------------
topL, topR = st.columns([1.5, 1])

with topR:
    run_id = st.session_state.get("run_id", f"run-{uuid.uuid4().hex[:10]}")
    st.session_state["run_id"] = run_id
    st.markdown(
        f"""
        <div class='card'>
          <div class='smallcaps'>run id</div>
          <div class='mono'>{run_id}</div>
          <div class='smallcaps' style='margin-top:10px;'>selected plan</div>
          <div class='mono'>{plan_path}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )

with topL:
    st.markdown("### Execute")
    st.markdown(
        "<div class='card'><div class='muted'>Runs the selected validation plan and generates a procedural record (JSON logs) + summary reports (MD/CSV).</div></div>",
        unsafe_allow_html=True,
    )
    run_clicked = st.button("Run Test Plan", use_container_width=True)

# -----------------------
# Run backend
# -----------------------
if run_clicked:
    start = time.time()
    env = os.environ.copy()
    env["FORGELAB_RUN_ID"] = run_id
    env["FORGELAB_SEED"] = str(seed)
    env["FORGELAB_INJECT_FAILURES"] = "1" if inject else "0"
    env["FORGELAB_VERBOSE"] = "1" if verbose else "0"

    cmd = [sys.executable, "-m", "app", "--plan", plan_path]
    p = subprocess.run(cmd, capture_output=True, text=True, env=env)

    st.session_state["last_rc"] = p.returncode
    st.session_state["last_stdout"] = p.stdout or ""
    st.session_state["last_stderr"] = p.stderr or ""
    st.session_state["last_duration_s"] = round(time.time() - start, 3)

# -----------------------
# Load latest log/report for status
# -----------------------
logs, rmd, csvs = latest_artifacts()
latest_log_obj = try_parse_json(logs[0]) if logs else None
status_from_log = extract_overall_status(latest_log_obj)

rc = st.session_state.get("last_rc", 0)

# Determine displayed status (fix "FAIL always")
if status_from_log in ("PASS", "FAIL", "WARN", "WARNING"):
    displayed_status = "WARN" if status_from_log == "WARNING" else status_from_log
else:
    # no explicit status found; base on rc but optionally soften
    if rc == 0:
        displayed_status = "PASS"
    else:
        displayed_status = "WARN" if demo_mode else "FAIL"

# -----------------------
# Operational Metrics
# -----------------------
st.markdown("### Operational Metrics")
m1, m2, m3, m4 = st.columns(4)
m1.metric("Last run status", displayed_status)
m2.metric("Duration (s)", st.session_state.get("last_duration_s", 0.0))
m3.metric("Failure injection", "ON" if inject else "OFF")
m4.metric("Seed", int(seed))

# -----------------------
# Output / Errors
# -----------------------
out_col, err_col = st.columns([1, 1])
with out_col:
    st.markdown("### Execution Output")
    stdout = st.session_state.get("last_stdout", "")
    st.code(stdout if stdout.strip() else "No stdout", language="text")

with err_col:
    st.markdown("### Errors")
    stderr = st.session_state.get("last_stderr", "")
    st.code(stderr if stderr.strip() else "No errors", language="text")

# -----------------------
# Artifacts: clean 3-column layout (fix bad layout)
# -----------------------
st.markdown("## Artifacts")

c1, c2, c3 = st.columns(3)

with c1:
    st.markdown("<div class='artifactBox'><div class='smallcaps'>latest log (json)</div>", unsafe_allow_html=True)
    if logs:
        st.write(pathlib.Path(logs[0]).name)
        obj = latest_log_obj
        st.markdown("<div class='artifactScroll'>", unsafe_allow_html=True)
        if isinstance(obj, dict):
            st.json(obj, expanded=False)
        else:
            st.code(read_tail(logs[0]), language="json")
        st.markdown("</div>", unsafe_allow_html=True)
    else:
        st.write("No logs found yet.")
    st.markdown("</div>", unsafe_allow_html=True)

with c2:
    st.markdown("<div class='artifactBox'><div class='smallcaps'>latest report (md)</div>", unsafe_allow_html=True)
    if rmd:
        st.write(pathlib.Path(rmd[0]).name)
        st.markdown("<div class='artifactScroll'>", unsafe_allow_html=True)
        st.markdown(read_tail(rmd[0], max_lines=320))
        st.markdown("</div>", unsafe_allow_html=True)
    else:
        st.write("No reports found yet.")
    st.markdown("</div>", unsafe_allow_html=True)

with c3:
    st.markdown("<div class='artifactBox'><div class='smallcaps'>latest metrics (csv)</div>", unsafe_allow_html=True)
    if csvs:
        st.write(pathlib.Path(csvs[0]).name)
        st.markdown("<div class='artifactScroll'>", unsafe_allow_html=True)
        st.code(read_tail(csvs[0], max_lines=80), language="text")
        st.markdown("</div>", unsafe_allow_html=True)
    else:
        st.write("No CSV metrics found yet.")
    st.markdown("</div>", unsafe_allow_html=True)

# -----------------------
# Enhanced panels (failure modes / timeline / top signals)
# -----------------------
st.markdown("## Failure Modes (Detected)")
samples = normalize_samples(latest_log_obj) if isinstance(latest_log_obj, dict) else []
events = normalize_events(latest_log_obj) if isinstance(latest_log_obj, dict) else []
failures, from_backend = infer_failure_modes(latest_log_obj or {}, samples)

if failures:
    st.markdown("<div class='card'>", unsafe_allow_html=True)
    st.markdown(
        f"<div class='smallcaps'>source</div><div class='mono'>{'backend log' if from_backend else 'telemetry inference'}</div>",
        unsafe_allow_html=True,
    )
    for f in failures:
        cls = "bad" if any(x in f.lower() for x in ["risk", "sag", "stall", "fail", "error"]) else "warn"
        st.markdown(f"<span class='pill {cls} mono'>{f}</span>", unsafe_allow_html=True)
    st.markdown("</div>", unsafe_allow_html=True)
else:
    st.markdown("<div class='card muted'>No failure modes detected yet. Run Thermal Stress Test with failure injection ON to demo RCA.</div>", unsafe_allow_html=True)

st.markdown("## Procedural Record Timeline")
if events:
    st.markdown("<div class='card'>", unsafe_allow_html=True)
    for idx, e in enumerate(events[:30], start=1):
        name = e.get("name") or f"step_{idx}"
        status = (e.get("status") or "OK").strip()
        detail = e.get("detail")
        badge = "ok"
        if status.lower() in ("fail", "failed", "error"):
            badge = "bad"
        elif status.lower() in ("warn", "warning"):
            badge = "warn"

        st.markdown(
            f"""
            <div style="display:flex; justify-content:space-between; align-items:center; margin-top:8px;">
              <div class="mono">{idx:02d}. {name}</div>
              <div class="pill {badge} mono">{status.upper()}</div>
            </div>
            """,
            unsafe_allow_html=True,
        )
        if detail:
            st.markdown(f"<div class='muted mono' style='margin-left:4px;'>{detail}</div>", unsafe_allow_html=True)
    st.markdown("</div>", unsafe_allow_html=True)
else:
    st.markdown("<div class='card muted'>No procedural steps found in latest log (expected keys: events/procedure/steps/timeline).</div>", unsafe_allow_html=True)

st.markdown("## Top Signals (Telemetry Summary)")
if samples:
    cpu_temp = extract_signal_series(samples, ["cpu_temp_c", "cpu_temp", "cpu_temperature_c"])
    psu_v = extract_signal_series(samples, ["psu_voltage_v", "psu_voltage", "v_psu"])
    fan_rpm = extract_signal_series(samples, ["fan_rpm", "rpm_fan", "fan0_rpm"])

    rows = []
    for label, series in [
        ("CPU Temp (C)", cpu_temp),
        ("PSU Voltage (V)", psu_v),
        ("Fan RPM", fan_rpm),
    ]:
        stats = series_stats(series)
        if stats:
            rows.append(
                {
                    "Signal": label,
                    "Min": round(stats["min"], 3),
                    "Avg": round(stats["avg"], 3),
                    "Max": round(stats["max"], 3),
                    "Trend": stats["trend"],
                    "Samples": len(series),
                }
            )

    if rows:
        st.dataframe(rows, use_container_width=True, hide_index=True)
        st.caption("Trend: ↗ increasing, ↘ decreasing, → stable")
    else:
        st.markdown("<div class='card muted'>Telemetry present but expected numeric keys not found.</div>", unsafe_allow_html=True)
else:
    st.markdown("<div class='card muted'>No telemetry samples found in latest log (expected keys: samples/telemetry/signals/metrics).</div>", unsafe_allow_html=True)

st.markdown("---")
st.markdown("<div class='smallcaps'>recruiter demo script</div>", unsafe_allow_html=True)
st.write("Run Thermal Stress Test (failure injection ON) → show Failure Modes → show Timeline → show Top Signals trend → open report artifact.")
