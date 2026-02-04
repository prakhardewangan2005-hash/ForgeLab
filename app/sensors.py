import math
import random

class VirtualHardware:
    """
    Simulates physical hardware behavior including thermal thermodynamics,
    power draw physics, and firmware states.
    """
    def __init__(self):
        # Initial State
        self.cpu_temp_c = 35.0
        self.cpu_freq_ghz = 3.2
        self.cpu_throttle = False
        self.fan_rpm = 2000
        self.psu_voltage_v = 12.0
        self.psu_current_a = 5.0
        self.psu_power_w = 60.0
        self.boot_stage = "OFF" # OFF, POST, UEFI, GRUB, KERNEL, OS
        self.os_health = "OK"
        
        # Physics Constants
        self.thermal_mass = 0.8 
        self.cooling_efficiency = 0.05
        self.base_freq = 3.2
        
    def update(self, load_percent: int, injection_map: dict):
        """
        Ticks the simulation physics forward by one step.
        """
        # 1. Apply Failures/Injections
        fan_stall = injection_map.get('fan_stall', False)
        psu_sag = injection_map.get('psu_sag', False)
        overheat_inject = injection_map.get('overheat', False)
        fw_hang = injection_map.get('fw_hang', False)

        # 2. Calculate Power (Load dependent)
        base_power = 60.0
        load_power = (load_percent / 100.0) * 200.0
        self.psu_power_w = base_power + load_power
        
        # 3. Calculate Voltage (Sag simulation)
        target_voltage = 11.0 if psu_sag else 12.0
        # Smooth transition
        self.psu_voltage_v = (self.psu_voltage_v * 0.8) + (target_voltage * 0.2)
        self.psu_current_a = self.psu_power_w / self.psu_voltage_v

        # 4. Fan Control (PID-ish)
        target_rpm = 2000 + (load_percent * 50)
        if fan_stall:
            target_rpm = 0
        self.fan_rpm = int((self.fan_rpm * 0.9) + (target_rpm * 0.1))

        # 5. Thermal Physics
        # Heat generation
        heat_gen = (self.psu_power_w * 0.4) 
        if overheat_inject:
            heat_gen += 100.0
            
        # Cooling (RPM dependent)
        cooling = (self.fan_rpm / 8000.0) * (self.cpu_temp_c - 25.0) * 2.0
        
        delta_temp = (heat_gen - cooling) * (1.0 - self.thermal_mass)
        self.cpu_temp_c += delta_temp

        # 6. Throttling Logic
        if self.cpu_temp_c > 95.0:
            self.cpu_throttle = True
            self.cpu_freq_ghz = 1.2 # Throttle down
        elif self.cpu_temp_c < 85.0:
            self.cpu_throttle = False
            self.cpu_freq_ghz = self.base_freq

        # 7. Boot/OS Logic
        if fw_hang and self.boot_stage != "OS":
            pass # Stuck
        elif self.boot_stage == "OS":
            self.os_health = "CRITICAL" if self.cpu_temp_c > 105.0 else "OK"

    def get_telemetry(self):
        return {
            "cpu_temp_c": round(self.cpu_temp_c, 2),
            "cpu_freq_ghz": round(self.cpu_freq_ghz, 2),
            "cpu_throttle": self.cpu_throttle,
            "fan_rpm": self.fan_rpm,
            "psu_voltage_v": round(self.psu_voltage_v, 2),
            "psu_power_w": round(self.psu_power_w, 2),
            "boot_stage": self.boot_stage,
            "os_health": self.os_health
        }
