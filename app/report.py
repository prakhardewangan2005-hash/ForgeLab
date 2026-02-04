import csv
import os
from datetime import datetime

class ReportGenerator:
    def __init__(self, run_id, telemetry, findings, failed_steps, output_dir="reports"):
        self.run_id = run_id
        self.telemetry = telemetry
        self.findings = findings
        self.failed_steps = failed_steps
        self.output_dir = output_dir
        os.makedirs(output_dir, exist_ok=True)

    def generate(self):
        self._write_csv()
        self._write_markdown()

    def _write_csv(self):
        filename = os.path.join(self.output_dir, f"{self.run_id}_metrics.csv")
        if not self.telemetry:
            return
            
        keys = self.telemetry[0].keys()
        with open(filename, 'w', newline='') as f:
            writer = csv.DictWriter(f, fieldnames=keys)
            writer.writeheader()
            writer.writerows(self.telemetry)
        print(f"CSV Report generated: {filename}")

    def _write_markdown(self):
        filename = os.path.join(self.output_dir, f"{self.run_id}_summary.md")
        status = "FAIL" if self.failed_steps else "PASS"
        
        with open(filename, 'w') as f:
            f.write(f"# ForgeLab-RTP Test Report\n")
            f.write(f"**Run ID:** {self.run_id}\n\n")
            f.write(f"**Overall Status:** {status}\n\n")
            
            f.write("## 1. Execution Summary\n")
            if self.failed_steps:
                f.write("The following steps failed validation criteria:\n")
                for step in self.failed_steps:
                    f.write(f"- {step}\n")
            else:
                f.write("All steps completed successfully.\n")
            
            f.write("\n## 2. Root Cause Analysis (RCA)\n")
            f.write("Automated analysis of sensor telemetry:\n")
            for finding in self.findings:
                f.write(f"- {finding}\n")
                
            f.write("\n## 3. Peak Statistics\n")
            max_temp = max(d['cpu_temp_c'] for d in self.telemetry)
            max_power = max(d['psu_power_w'] for d in self.telemetry)
            f.write(f"- **Max CPU Temp:** {max_temp} C\n")
            f.write(f"- **Max Power Draw:** {max_power} W\n")

        print(f"Markdown Report generated: {filename}")
