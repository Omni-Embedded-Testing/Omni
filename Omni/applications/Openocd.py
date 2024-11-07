import subprocess
import argparse
import time
from datetime import datetime
import Omni.process_manager.process_manager as process_manager
import re
import psutil
import json

def is_port_open(port, protocol='tcp'):
    connections = psutil.net_connections(kind=protocol)
    for conn in connections:
        if conn.laddr.port == port:
            return True
    return False

def is_pid_running(pid):
    return psutil.pid_exists(pid)

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
    }
    process_manager.append_process_data_to_file(
        open_ocd_process_entry, process_file)
    process_manager.pretty_print_json(open_ocd_process_entry)


def verify_openocd(proccess_data_file)->bool:
    with open(proccess_data_file, 'r') as file:
        backend_processes = json.load(file)
    if not backend_processes:
        raise ProcessStartupError("No backend processes found in the process data file ${proccess_data_file}.")
    if "pid" in backend_processes[0]:
        open_ocd_pid= int(backend_processes[0]["pid"])
        if(is_pid_running(open_ocd_pid)):
            print(f"Openocd is running with PID {str(open_ocd_pid)}.")
        else:
            print(f"PID {str(open_ocd_pid)} is not running.")
            return False
    else:
        raise ProcessStartupError("File ${proccess_data_file} malformed pid entry not present.")
    if "port" in backend_processes[0]:
            port= backend_processes[0]["port"]
            if is_port_open(port):
                print(f"OpenOCD listening on Port {port}")
                return True
            else:
                print(f"OpenOCD not listening on Port {port}")
                return False
    else:
        raise ProcessStartupError("File ${proccess_data_file} malformed pid entry not present.")
        
    return True

def read_log(log_file_path):
    with open(log_file_path, 'r') as log:
        file_contents = log.read()
    return file_contents


# Call from folder: embedded-integration-test-framework
# Example Call: python3 -m Omni.applications.Openocd --path /usr/bin/openocd --log ./.Transfer_Area/OpenOcdLog.txt --board /usr/share/openocd/scripts/board/stm32f4discovery.cfg --interface /usr/share/openocd/scripts/interface/stlink-v2.cfg --proc ./.Process_Info/CmdlineOpenOcd.txt
if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--path', type=str,
                        help='Path to the Openocd Application')
    parser.add_argument('--log', type=str,
                        help='Path to file where the Salea log will be saved')
    parser.add_argument(
        '--board', type=str, help='Port that will be exposed by the salea application')
    parser.add_argument('--interface', type=str,
                        help='Path to file where process information will be saved')
    parser.add_argument(
        '--proc', type=str, help='Path to file where process information will be saved')

    args = parser.parse_args()
    process_manager.create_config_file(args.proc)
    launch_openocd(args.proc, args.path, args.board, args.interface, args.log)
    time.sleep(10)
