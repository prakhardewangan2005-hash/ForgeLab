class RootCauseAnalyzer:
    """
    Analyzes telemetry history to determine root cause of failures.
    """
    def __init__(self, telemetry_data):
        self.data = telemetry_data

    def analyze(self):
        findings = []
        
        # Thresholds
        TEMP_CRITICAL = 95.0
        VOLTAGE_LOW = 11.4
        FAN_STALL_RPM = 100

        for idx, entry in enumerate(self.data):
            # Thermal Analysis
            if entry['cpu_temp_c'] > TEMP_CRITICAL:
                if entry['fan_rpm'] < FAN_STALL_RPM:
                    findings.append(f"T={idx}s: Thermal Excursion caused by Fan Stall (RPM={entry['fan_rpm']})")
                elif entry['active_load'] > 90:
                    findings.append(f"T={idx}s: Thermal Saturation under High Load ({entry['active_load']}%)")
                else:
                    findings.append(f"T={idx}s: Unexplained Thermal Spikes")

            # Power Analysis
            if entry['psu_voltage_v'] < VOLTAGE_LOW:
                findings.append(f"T={idx}s: PSU Voltage Sag detected ({entry['psu_voltage_v']}V)")

            # Throttling
            if entry['cpu_throttle']:
                findings.append(f"T={idx}s: CPU Throttling Active")

        # Deduplicate and summarize
        unique_findings = sorted(list(set(findings)))
        return unique_findings if unique_findings else ["No Anomalies Detected"]
