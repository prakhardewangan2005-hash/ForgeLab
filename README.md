# ForgeLab-RTP

**System-Level Server Bring-Up, Thermal & Power Validation Platform**

ForgeLab-RTP is a production-style Release-to-Production (RTP) validation and debug platform designed to mirror how hyperscale infrastructure teams validate new server hardware before fleet rollout. The system automates bring-up checks, thermal and power stress testing, failure injection, procedural logging, and root-cause analysis using deterministic, reproducible runs.

This project focuses on *system-level ownership* rather than isolated components, emphasizing observability, failure modes, and operational correctness across CPU, power, cooling, firmware, and OS layers.

---

### 🔗 Live Demo (Browser-Only, No Terminal)
**Streamlit Cloud Demo:**  
👉 https://forgelab-3esypw3tvcrbqbrrc2umfe.streamlit.app/

The live demo allows you to:
- Select a system-level test plan (Bring-Up / Thermal / Power)
- Execute validation runs remotely
- Observe real-time execution output
- Inspect generated logs, reports, and metrics
- Review detected failure modes, procedural timelines, and top telemetry signals

---

### 🧠 What This Demonstrates
- System-level hardware bring-up and validation workflows
- Thermal and power stress testing under controlled conditions
- Failure injection and reproducible fault analysis
- Structured procedural records and data logs
- Root-cause analysis driven by telemetry correlation
- Operational metrics suitable for RTP sign-off decisions

---

### 🧩 System Components Modeled
- **CPU:** temperature, throttling risk, thermal trends  
- **Power:** PSU voltage sag, stability under load  
- **Cooling:** fan RPM behavior and airflow degradation  
- **Firmware:** bring-up sequencing and failure detection  
- **OS:** runtime health signals and execution state  

---

### ⚙️ Test Plans
All validations are driven by YAML-based system test plans:
- `bringup.yaml` — firmware → OS bring-up validation
- `thermal.yaml` — sustained thermal stress testing
- `power.yaml` — power delivery and voltage stability checks

Each plan executes as a deterministic run with a unique run ID and complete procedural record.

---

### 📊 Outputs & Artifacts
Every run generates:
- **JSON logs** (`logs/`) — full procedural and telemetry records
- **Markdown reports** (`reports/`) — human-readable RTP summaries
- **CSV metrics** (`reports/`) — numerical telemetry for analysis

Artifacts are viewable directly in the live demo interface.

---

### 🔍 Failure Analysis
ForgeLab-RTP identifies and surfaces:
- Thermal throttle risk
- PSU voltage sag
- Fan stall or degraded cooling
- Bring-up step failures
- Execution anomalies

Failures are detected either directly from backend logs or inferred from telemetry trends, mirroring real-world debug workflows.

---

### 🚀 How to Run (Local)

pip install -r requirements.txt
python -m app --plan testplans/thermal.yaml

---

### 🎯 Why This Project
This project was built to reflect how hardware systems engineers work in real production environments:
- Emphasis on automation over manual testing
- Clear operational metrics instead of academic benchmarks
- Failure-first design to validate system robustness
- Tooling designed for scale, repeatability, and auditability

ForgeLab-RTP is intentionally scoped as an internal-style validation tool rather than a demo app, prioritizing realism, correctness, and ownership.

---

### 📌 Status
Active — continuously extended with additional failure modes, telemetry signals, and validation coverage.
