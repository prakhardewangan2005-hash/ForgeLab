import time
import yaml
import logging
from .sensors import VirtualHardware
from .failures import FailureInjector

logger = logging.getLogger("ForgeLab")

class TestRunner:
    def __init__(self, plan_path):
        self.plan_path = plan_path
        self.hardware = VirtualHardware()
        self.injector = FailureInjector()
        self.telemetry_history = []
        self.test_plan = self._load_plan()
        self.failed_steps = []

    def _load_plan(self):
        with open(self.plan_path, 'r') as f:
            return yaml.safe_load(f)

    def execute(self):
        logger.info(f"Starting Test Plan: {self.test_plan.get('name', 'Unknown')}")
        steps = self.test_plan.get('steps', [])
        
        start_time = time.time()
        
        for step in steps:
            step_name = step.get('name')
            duration = step.get('duration', 1)
            action = step.get('action')
            params = step.get('params', {})
            
            logger.info(f"Executing Step: {step_name} | Action: {action} | Duration: {duration}s")
            
            # Handle Actions
            if action == 'boot':
                self._simulate_boot(duration)
            elif action == 'stress':
                self._run_loop(duration, load=params.get('load', 50))
            elif action == 'inject_failure':
                self.injector.set_injection(params.get('type'), True)
                self._run_loop(duration, load=params.get('load', 10))
            elif action == 'clear_failure':
                self.injector.set_injection(params.get('type'), False)
                self._run_loop(duration, load=params.get('load', 10))
            
            # Validate Step Criteria
            if not self._validate_criteria(step.get('criteria', {})):
                logger.error(f"Step Failed: {step_name}")
                self.failed_steps.append(step_name)
            else:
                logger.info(f"Step Passed: {step_name}")

        total_time = time.time() - start_time
        logger.info(f"Test Plan Completed in {total_time:.2f}s")
        return self.telemetry_history, self.failed_steps

    def _simulate_boot(self, duration):
        stages = ["POST", "UEFI", "GRUB", "KERNEL", "OS"]
        stage_duration = duration / len(stages)
        for stage in stages:
            self.hardware.boot_stage = stage
            self._run_loop(stage_duration, load=20)

    def _run_loop(self, duration, load):
        # Simulation runs at 10x speed (0.1s sleep = 1s sim time)
        ticks = int(duration)
        for _ in range(ticks):
            self.hardware.update(load, self.injector.get_active())
            data = self.hardware.get_telemetry()
            data['timestamp'] = time.time()
            data['active_load'] = load
            data['injections'] = str([k for k,v in self.injector.get_active().items() if v])
            self.telemetry_history.append(data)
            time.sleep(0.05) # Speed up simulation for CLI UX

    def _validate_criteria(self, criteria):
        if not criteria:
            return True
        
        latest = self.hardware.get_telemetry()
        
        if 'max_temp' in criteria and latest['cpu_temp_c'] > criteria['max_temp']:
            logger.warning(f"Validation Fail: Temp {latest['cpu_temp_c']} > {criteria['max_temp']}")
            return False
            
        if 'min_voltage' in criteria and latest['psu_voltage_v'] < criteria['min_voltage']:
            logger.warning(f"Validation Fail: Voltage {latest['psu_voltage_v']} < {criteria['min_voltage']}")
            return False

        if 'os_running' in criteria and criteria['os_running'] and latest['os_health'] != "OK":
            logger.warning("Validation Fail: OS Health not OK")
            return False
            
        return True
