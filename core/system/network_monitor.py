import subprocess
import socket
import sys

class NetworkMonitor:
    def __init__(self):
        self.interface_name = "Wi-Fi"  # Default fallback

    def check_internet(self, host="8.8.8.8", port=53, timeout=3):
        try:
            socket.setdefaulttimeout(timeout)
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                s.connect((host, port))
            return True
        except socket.error:
            return False

    def get_wifi_details(self):
        try:
            output = subprocess.check_output("netsh wlan show interfaces", shell=True, text=True, errors='ignore')
            ssid = None
            state = "disconnected"
            name = "Wi-Fi"
            for line in output.split("\n"):
                line = line.strip()
                if line.startswith("SSID") or line.startswith("SSID "):
                    parts = line.split(":", 1)
                    if len(parts) > 1:
                        ssid = parts[1].strip()
                elif line.startswith("State") or line.startswith("State "):
                    parts = line.split(":", 1)
                    if len(parts) > 1:
                        state = parts[1].strip()
                elif line.startswith("Name") or line.startswith("Name "):
                    parts = line.split(":", 1)
                    if len(parts) > 1:
                        name = parts[1].strip()
            
            self.interface_name = name
            return {"state": state, "ssid": ssid, "interface": name}
        except Exception:
            return {"state": "unknown", "ssid": None, "interface": self.interface_name}

    def check_wifi(self):
        details = self.get_wifi_details()
        internet = "online" if self.check_internet() else "offline"
        if details["state"] == "connected" and details["ssid"]:
            return f"Wi-Fi connected to '{details['ssid']}' on interface '{details['interface']}'. Internet is {internet}."
        else:
            return f"Wi-Fi is {details['state']}. Internet is {internet}."

    def toggle_wifi(self, state="on"):
        self.get_wifi_details()
        admin_status = "enabled" if state.lower() in ["on", "enable", "enabled"] else "disabled"
        cmd = f'netsh interface set interface name="{self.interface_name}" admin={admin_status}'
        
        try:
            # Try executing
            result = subprocess.run(cmd, shell=True, text=True, capture_output=True, timeout=5)
            if result.returncode == 0:
                return f"Wi-Fi interface '{self.interface_name}' set to {admin_status} successfully."
            else:
                # If command fails (most likely due to permission), prompt for privilege elevation
                ps_cmd = f"Start-Process cmd -ArgumentList '/c {cmd}' -Verb RunAs"
                subprocess.run(["powershell", "-Command", ps_cmd], check=True)
                return f"Requested Administrator privileges to turn Wi-Fi {state}. Please check the UAC pop-up."
        except Exception as e:
            return f"Failed to toggle Wi-Fi: {str(e)}"
