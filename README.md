# ForgeLab-RTP

**ForgeLab-RTP** is a backend validation framework designed for system-level server bring-up, thermal/power testing, and automated root cause analysis. It simulates hardware physics (thermodynamics, power electronics) and firmware states to validate test logic without requiring physical hardware access.

## Features

*   **Deterministic Simulation**: Simulates CPU temperature, throttling, fan PID loops, and PSU voltage sag.
*   **YAML Test Plans**: Define steps, stress loads, and pass/fail criteria declaratively.
*   **Failure Injection**: Programmatically inject fan stalls, PSU sags, and firmware hangs.
*   **Automated RCA**: Post-run analysis correlates sensor logs to identify why a test failed (e.g., "Thermal Excursion due to Fan Stall").
*   **Reporting**: Generates structured JSON logs, CSV metrics, and Markdown summaries.

## Installation

Requires Python 3.10+.

```bash
pip install -r requirements.txt
