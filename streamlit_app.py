import os
import sys
import subprocess
import pathlib
import streamlit as st

st.set_page_config(page_title="ForgeLab-RTP", layout="wide")

st.title("ForgeLab-RTP")
st.caption("System-Level Server Bring-Up, Thermal & Power Validation Platform")

PLAN_OPTIONS = {
    "Bring-Up Validation": "testplans/bringup.yaml",
    "Thermal Stress Test": "testplans/thermal.yaml",
    "Power Validation": "testplans/power.yaml",
}

plan_name = st.selectbox("Select test plan", list(PLAN_OPTIONS.keys()))
plan_path = PLAN_OPTIONS[plan_name]

if st.button("Run Test Plan"):
    os.makedirs("logs", exist_ok=True)
    os.makedirs("reports", exist_ok=True)

    cmd = [sys.executable, "-m", "app", "--plan", plan_path]
    result = subprocess.run(cmd, capture_output=True, text=True)

    st.subheader("Execution Output")
    st.code(result.stdout if result.stdout else "No stdout")

    if result.stderr:
        st.subheader("Errors")
        st.code(result.stderr)

    st.subheader("Generated Reports")
    reports = pathlib.Path("reports")
    if reports.exists():
        for f in sorted(reports.glob("*")):
            st.write(f.name)
