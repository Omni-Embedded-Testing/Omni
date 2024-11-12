import subprocess
from datetime import datetime
import Omni.process_manager.process_manager as process_manager

class ProcessStartupError(Exception):
    def __init__(self, message):
        super().__init__(message)

    def __str__(self):
        error_message = super().__str__()
        if self.error_code is not None:
            return f"{error_message}"
        return error_message

def launch_openocd(process_file, openocd_path, arguments, open_ocd_log_path):
    process_manager.verify_file(process_file)
    openocd_log_fd = open(open_ocd_log_path, 'w')
    open_ocd_launch = [openocd_path] + arguments
    process = subprocess.Popen(
        open_ocd_launch, stdout=openocd_log_fd, stderr=openocd_log_fd)
    openocd_jobpid = str(process.pid)
    current_time = datetime.now().strftime("%H:%M:%S")
    open_ocd_process_entry = {
        "application": "Open OCD",
        "pid": openocd_jobpid,
        "log_file": open_ocd_log_path,
        "process_call": " ".join(open_ocd_launch),
        "start_time": current_time,
        "port": 3333,
        "pgrep_string": "openocd",
        "status": "started",
    }
    process_manager.append_process_data_to_file(
        open_ocd_process_entry, process_file)
    process_manager.pretty_print_json(open_ocd_process_entry)
    
