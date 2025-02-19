import os
import subprocess
import threading
import time
import psutil
from PyQt5.QtCore import QObject, pyqtSignal

class BackendMonitor(QObject):
    error_signal = pyqtSignal(str)  # Signal to notify the UI of backend failure

    def __init__(self):
        super().__init__()
        self.base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "../be"))
        self.script_path = os.path.join(self.base_dir, "binocular-tension-be.py")
        self.process = None  # Store backend process reference
        self.restart_attempts = 0  # Track restart attempts
        self.max_retries = 3  # Maximum restart attempts

        # Start the monitoring thread
        self.monitor_thread = threading.Thread(target=self.monitor_backend, daemon=True)
        self.monitor_thread.start()

    def is_backend_running(self):
        """Check if binocular-tension-be.py is currently running."""
        script_name = "binocular-tension-be.py"

        for process in psutil.process_iter(attrs=['pid', 'name', 'cmdline']):
            try:
                cmdline = process.info['cmdline']
                if cmdline and any(os.path.basename(arg) == script_name for arg in cmdline):
                    return True  # Backend is running
            except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
                continue

        return False  # Backend is not running
    
    def restart_backend(self):
        """Restart the backend process if it's not running."""
        self.force_close_backend()  # Ensure old instances are stopped before restarting

        if self.restart_attempts < self.max_retries:
            print(f"Restart attempt {self.restart_attempts + 1}/{self.max_retries}")
            self.process = subprocess.Popen(['python', self.script_path], cwd=self.base_dir)
            
            # Wait briefly and check if it successfully started
            time.sleep(10)  # Give it a moment to start
            if self.is_backend_running():
                print("Backend restarted successfully. Resetting restart attempts.")
                self.restart_attempts = 0  # Reset counter on success
            else:
                self.restart_attempts += 1  # Only increment on failure

        else:
            print("Max restart attempts reached. Sending error signal.")
            self.error_signal.emit("Backend failed to start after multiple attempts.")

    def force_close_backend(self):
        """Forcefully stop all instances of binocular-tension-be.py."""
        script_name = "binocular-tension-be.py"

        for process in psutil.process_iter(attrs=['pid', 'name', 'cmdline']):
            try:
                cmdline = process.info['cmdline']
                if cmdline and any(os.path.basename(arg) == script_name for arg in cmdline):
                    process.terminate()  # Terminate process
                    process.wait()  # Ensure process stops completely
            except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
                continue

    def monitor_backend(self):
        """Monitor and restart the backend every 30 seconds if needed."""
        while True:
            if not self.is_backend_running():
                print("Backend is not running. Restarting...")
                self.restart_backend()
            time.sleep(30)  # Wait 30 seconds before checking again
