class FailureInjector:
    """
    Manages active failure injections based on test plan instructions.
    """
    def __init__(self):
        self.active_injections = {
            "fan_stall": False,
            "psu_sag": False,
            "overheat": False,
            "fw_hang": False
        }

    def set_injection(self, injection_type: str, state: bool):
        if injection_type in self.active_injections:
            self.active_injections[injection_type] = state
            return True
        return False

    def get_active(self):
        return self.active_injections
