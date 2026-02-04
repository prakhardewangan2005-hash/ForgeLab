import argparse
import sys
import os
from datetime import datetime
from .utils import setup_logging
from .runner import TestRunner
from .rca import RootCauseAnalyzer
from .report import ReportGenerator

def main():
    parser = argparse.ArgumentParser(description="ForgeLab-RTP: Hardware Validation Platform")
    parser.add_argument("--plan", type=str, required=True, help="Path to YAML test plan")
    args = parser.parse_args()

    if not os.path.exists(args.plan):
        print(f"Error: Plan file '{args.plan}' not found.")
        sys.exit(1)

    # Setup
    logger, log_file = setup_logging()
    run_id = os.path.basename(log_file).replace(".json", "")
    
    # Execution
    runner = TestRunner(args.plan)
    try:
        telemetry, failed_steps = runner.execute()
    except Exception as e:
        logger.exception("Fatal error during execution")
        sys.exit(1)

    # Analysis
    logger.info("Running Root Cause Analysis...")
    rca = RootCauseAnalyzer(telemetry)
    findings = rca.analyze()

    # Reporting
    logger.info("Generating Reports...")
    reporter = ReportGenerator(run_id, telemetry, findings, failed_steps)
    reporter.generate()

    # Exit Code
    sys.exit(1 if failed_steps else 0)
