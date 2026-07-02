import os
import subprocess
import psutil
import socket

class SystemAgent:
    def __init__(self):
        pass

    def open_app(self, app_name):
        app_name = app_name.lower().strip()
        try:
            if "chrome" in app_name:
                # Direct windows start command for Chrome
                subprocess.Popen("cmd /c start chrome", shell=True)
                return "Opening Google Chrome."
            elif "code" in app_name or "vs code" in app_name or "vscode" in app_name:
                subprocess.Popen("cmd /c code", shell=True)
                return "Opening VS Code."
            elif "spotify" in app_name:
                subprocess.Popen("cmd /c start spotify:", shell=True)
                return "Opening Spotify."
            else:
                # Attempt generic shell execution
                # We sanitize the input to prevent arbitrary execution outside opening programs
                clean_name = "".join(c for c in app_name if c.isalnum() or c in [' ', '-', '_'])
                subprocess.Popen(f"cmd /c start {clean_name}", shell=True)
                return f"Attempting to open {clean_name}."
        except Exception as e:
            return f"Failed to open application '{app_name}': {str(e)}"

    def close_app(self, app_name):
        app_name = app_name.lower().strip()
        # Map common names to process names
        mapping = {
            "chrome": "chrome.exe",
            "vs code": "code.exe",
            "vscode": "code.exe",
            "code": "code.exe",
            "spotify": "spotify.exe"
        }
        
        proc_name = mapping.get(app_name, f"{app_name}.exe")
        try:
            output = subprocess.check_output(f"taskkill /f /im {proc_name}", shell=True, stderr=subprocess.STDOUT)
            return f"Successfully closed {app_name}."
        except subprocess.CalledProcessError:
            return f"Could not find or close process for '{app_name}' (tried {proc_name})."

    def check_battery(self):
        try:
            battery = psutil.sensors_battery()
            if battery is None:
                return "Battery status is not available (is this a desktop PC?)."
            
            percent = battery.percent
            plugged = battery.power_plugged
            status = "plugged in and charging" if plugged else "running on battery power"
            return f"Your battery is at {percent}% and is currently {status}."
        except Exception as e:
            return f"Failed to check battery: {str(e)}"

    def check_wifi(self):
        try:
            # Query network interfaces
            output = subprocess.check_output("netsh wlan show interfaces", shell=True, text=True, errors='ignore')
            ssid = None
            state = "disconnected"
            for line in output.split("\n"):
                line = line.strip()
                if line.startswith("SSID"):
                    ssid = line.split(":", 1)[1].strip()
                elif line.startswith("State"):
                    state = line.split(":", 1)[1].strip()
            
            # Check internet connectivity
            internet = "online" if self._check_internet_connection() else "offline"
            
            if state == "connected" and ssid:
                return f"Wi-Fi is connected to '{ssid}'. Internet status is {internet}."
            else:
                return f"Wi-Fi status is currently {state}. Internet status is {internet}."
        except Exception as e:
            # Fallback to simple socket ping if netsh fails
            internet = "online" if self._check_internet_connection() else "offline"
            return f"Could not query Wi-Fi adapter details, but your internet status is {internet}."

    def _check_internet_connection(self, host="8.8.8.8", port=53, timeout=3):
        try:
            socket.setdefaulttimeout(timeout)
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                s.connect((host, port))
            return True
        except socket.error:
            return False

    def create_folder(self, folder_path):
        try:
            os.makedirs(folder_path, exist_ok=True)
            return f"Folder successfully created at: {folder_path}"
        except Exception as e:
            return f"Failed to create folder: {str(e)}"

    def run_command(self, command):
        try:
            # Dangerous execution restriction - we alert but allow simple utility queries
            # Avoid arbitrary dangerous commands
            restricted_keywords = ["rmdir /s", "del /f", "format", "shutdown"]
            if any(kw in command.lower() for kw in restricted_keywords):
                return "Command execution blocked: Contains restricted keywords for safety."
                
            result = subprocess.run(command, shell=True, text=True, capture_output=True, timeout=10)
            if result.returncode == 0:
                return f"Command executed successfully. Output:\n{result.stdout}"
            else:
                return f"Command failed with code {result.returncode}. Error:\n{result.stderr}"
        except Exception as e:
            return f"Failed to run command: {str(e)}"
