import json
import os
import subprocess
import psutil
from datetime import datetime
from pathlib import Path
from time import sleep
from rich.console import Console
from Omni.cli.console_animations import sleep_with_progress


# Function to extract each element's properties into a map with mandatory field check
def extract_backend_processes(process)->dict:
    mandatory_fields = ["name", "path","port","search_string", "arguments", "log_file"]
    # Check each field, and raise an error if it's missing
    for field in mandatory_fields:
        if field not in process or process[field] is None:
            raise ValueError(f"Entry '{field}' is mandatory. \n Process Entry Stream: '{process}'")
    return {
            "name": process.get("name"),
            "path": process.get("path"),
            "port": process.get("port"),
            "search_string": process.get("search_string"),
            "arguments": process.get("arguments"),
            "log_file": process.get("log_file")
        }

class InvalidProcessEntry(Exception):
    pass

class PortClosedError(Exception):
        pass


class ProcessManager:
    def __init__(self, _process_config_file):
        self.backend_config_file_path = _process_config_file
        self.backend_config_file_stream = self.load_config_file()
        self.backend_processes_data_file_name = self.fetch_backend_processes_data_file_name()
        self.backend_processes_data_path = Path(self.backend_config_file_path).parent / self.backend_processes_data_file_name
        self.backend_loaded_processes = None
        self.console = Console()
        

    def load_config_file(self):
        with open(self.backend_config_file_path, 'r') as file:
            backend_config_file = json.load(file)
        return backend_config_file
    
    def fetch_backend_processes_data_file_name(self):
        backend_processes_data_file = self.backend_config_file_stream.get('backend_processes_data_file')
        if backend_processes_data_file is None:
            raise KeyError(f"The configuration file '{self.backend_config_file_path}' does not contain 'backend_processes_data_file' entry")
        return backend_processes_data_file

    def create_backend_processes_data_file(self, base_path=None, overwrite_data_file=False):
        temp_backend_processes_data_path = self.__get_backend_processes_data_path(base_path)
        self.backend_processes_data_path=temp_backend_processes_data_path
        if self.check_file_exists(temp_backend_processes_data_path):
            if overwrite_data_file:
                print(f"Overwriting backend processes data file: {temp_backend_processes_data_path}")
                self._create_empty_process_file()
            else:
                self._error_msg_file_already_exists(temp_backend_processes_data_path)
        else:
            print(f"Backend processes data file path: {self.backend_processes_data_path}")
            self._create_empty_process_file()

    def __get_backend_processes_data_path(self, base_path):
        if base_path is not None:
            temp_backend_processes_data_path = Path(base_path) / Path(self.backend_processes_data_file_name)
        else:
            temp_backend_processes_data_path = self.backend_processes_data_path
        return temp_backend_processes_data_path
    
    def load_backend_processes_data_file(self, base_path=None):
        temp_backend_processes_data_path = self.__get_backend_processes_data_path(base_path)
        if self.check_file_exists(temp_backend_processes_data_path) is False:
            self._error_msg_file_doesnt_exist(temp_backend_processes_data_path)
        else:
            self.backend_processes_data_path=temp_backend_processes_data_path
            print(f"Backend processes data file path: {self.backend_processes_data_path}")
            self.backend_loaded_processes= self.__load_processes_from_data_file()
            print("Loaded processes:")
            self.pretty_print_json(self.backend_loaded_processes)
            

    def check_file_exists(self, file_path):
        return os.path.isfile(file_path)

    def _error_msg_file_already_exists(self, filename):
        raise RuntimeError(f"File '{filename}' already exists!")
    
    def _error_msg_file_doesnt_exist(self, filename):
        raise RuntimeError(f"File '{filename}' does not exists!")

    def launch_processes(self):
        backend_processes_array = self.backend_config_file_stream.get('backend_processes', [])
        for process in backend_processes_array:
            process_maped = extract_backend_processes(process)
            self.launch_process(process_maped)
    
    def launch_process(self,process_maped):
        log_path = Path(self.backend_processes_data_path).parent / Path(process_maped["log_file"])
        print(f"Log file path: {log_path}")
        with open(log_path, 'w') as log_fd:
            process_launch = [process_maped["path"]] + process_maped["arguments"]
            print(f"Launching process: {process_launch}")
            process = subprocess.Popen(process_launch, stdout=log_fd, stderr=log_fd)
            return_code = process.poll()
            self._eval_ret_code(process_maped, return_code)
            process_entry = self._build_process_entry(process_maped, process_launch, str(process.pid))
            self.pretty_print_json(process_entry)
            self.append_process_data_to_file(process_entry)

    def _eval_ret_code(self, process_maped, return_code):
        if return_code is None:
            print(f"Process '{process_maped['name']}' is running")
        else:
            raise RuntimeError(f"Process '{process_maped['name']}' has stopped with return code {return_code}")

    def _build_process_entry(self, process_maped, process_launch, process_pid):
        process_entry = {
            "name": process_maped["name"],
            "pid": process_pid,
            "log_file": process_maped["log_file"],
            "process_call": " ".join(process_launch),
            "start_time": datetime.now().strftime("%H:%M:%S.%f")[:-3],  
            "port": process_maped["port"],
            "search_string": process_maped["search_string"],
            "status": "running",
            }
        return process_entry


    def _create_empty_process_file(self):
        Path(self.backend_processes_data_path).parent.mkdir(parents=True, exist_ok=True)
        print(f"Creating empty backend processes data file: {self.backend_processes_data_path}")
        with open(self.backend_processes_data_path, "w") as json_file:
            json.dump([], json_file)

    def append_process_data_to_file(self, data):
        self._verify_valid_process_data(data)
        json_data = self.__load_processes_from_data_file()
        json_data.append(data)
        self.__save_processes_in_data_file(json_data)

    def __load_processes_from_data_file(self):
        with open(self.backend_processes_data_path, "r") as file:
            json_data = json.load(file)
        return json_data
    
    def _verify_valid_process_data(self, my_dict):
        minimal_keys_list = ["name", "pid", "search_string", "process_call"]
        if not all(key in my_dict for key in minimal_keys_list):
            raise InvalidProcessEntry(
                'Missing keys in process dictionary. Minimal expected Keys: ' + str(minimal_keys_list))
        
    def __save_processes_in_data_file(self, json_data):
        with open(self.backend_processes_data_path, "w") as file:
            json.dump(json_data, file, indent=4)

    def pretty_print_json(self, data):
        print(json.dumps(data, indent=4))

    def close_applications(self):
        for application in self.backend_loaded_processes:
            pid = application["pid"]
            print(f"Closing '{application['name']}'. Sending SIGTERM to pid: {pid}")
            print(f"application status: {application['status']}")
            if(application["status"] == "running"):
                terminated =self.__terminate_process_by_pid(int(pid))
                if terminated:
                    application["status"] = "terminate requested"
                    application["SIGTERM_time"] = datetime.now().strftime("%H:%M:%S.%f")[:-3],
                else:
                    self.console.print(f"Process '{application['name']}' with pid '{pid}' is not running or does not exist", style="bold red")
            else:
                self.console.print(f"Process '{application['name']}' with pid '{pid}' is not running", style="bold green")
        self.__save_processes_in_data_file(self.backend_loaded_processes)

    def __terminate_process_by_pid(self, pid: int):
        process= self.__get_process_handle(pid)
        if process is not None:
            process.terminate()
            return True
        else:
            print(f"Process with pid '{pid}' does not exist")
            return False
    

    def __get_process_handle(self, pid: int):
        try:
            process = psutil.Process(int(pid))
            return process
        except psutil.NoSuchProcess:
            return None

    def verify_application_termination(self,kill_delay=1):
        for application in self.backend_loaded_processes:
            pid = application["pid"]
            self.console.print(f"Verifying application '[bold cyan]{application['name']}[/bold cyan]' termination")
            process= self.__get_process_handle(pid)
            if process is None:
                self.console.print(f"[bold green]Process '{application['name']}' with pid '{pid}' is not in memory.[/bold green]")
                application["status"] = "terminated"
            else:
                status = process.status()
                if status == psutil.STATUS_ZOMBIE:
                    self.console.print(f"Process with PID {pid} is currently a zombie process.")
                    self.console.print(f"[bold green]Process '{application['name']}' with pid '{pid}' will be removed when Omni finishes execution.[/bold green]")
                else:
                    self.console.print(f"Process with PID {pid} has status {status}.")
                    self.console.print(f"[bold cyan]Requesting SIGKILL to process '{application['name']}' with pid '{pid}'[/bold cyan]")
                    self.__kill_application(application, kill_delay, process)                
            self.__save_processes_in_data_file(self.backend_loaded_processes)

    def __kill_application(self, application, kill_delay, process):
            pid = application["pid"]
            app_name = application["name"]
            # Log SIGKILL initiation
            self.console.print(f"[bold red]Sending SIGKILL to process '{app_name}' with pid '{pid}'[/bold red]")
            application["status"] = "SIGKILL requested"
            application["SIGKILL_time"] = datetime.now().strftime("%H:%M:%S.%f")[:-3]
            process.kill()
            sleep_with_progress(kill_delay, "SIGKILL delay")
            process_after_kill= self.__get_process_handle(pid)
            if process_after_kill is None:
                self.console.print(f"[bold green]Process '{app_name}' with pid '{pid}' has been terminated after SIGKILL.[/bold green]")
                application["status"] = "killed"
            else:
                status = process.status()
                if status == psutil.STATUS_ZOMBIE:
                    self.console.print(f"Process with PID {pid} is currently a zombie process.")
                    self.console.print(f"[bold green]Process '{application['name']}' with pid '{pid}' will be removed when Omni finishes execution.[/bold green]")
                    application["status"] = "killed"
                else:
                    self.console.print(f"[bold red]Process '{app_name}' with pid '{pid}' has not been terminated after SIGKILL.[/bold red]")
                    application["status"] = "SIGKILL FAILED"


    def verify_open_ports(self):
        backend_processes_array = self.backend_config_file_stream.get('backend_processes', [])
        for process in backend_processes_array:
            process_maped = extract_backend_processes(process)
            port = process_maped["port"]
            print(f"Verifying port '{port}' from application '{process_maped['name']}'")
            if self.__check_port_open(port) is False:
                raise PortClosedError(f"Port '{port}' from application '{process_maped['name']} is not open. Verify if the application is running")
            else:
                print(f"Port '{port}' from application is open")
        self.console.print("[green]All ports are open[/green]", style="bold green")
    
    def __check_port_open(self,port):
            for conn in psutil.net_connections(kind="inet"):
                if str(conn.laddr.port) == str(port):
                    return True
            return False


    def verify_file(self):
        self.__verify_file_exists(self.config_file)
        self.__verify_file_format(self.config_file)

    def __verify_file_exists(self, process_file):
        if not os.path.isfile(process_file):
            raise FileNotFoundError(f"file '{process_file}' not found")

    def __verify_file_format(self, process_file):
        with open(process_file, "r") as file:
            json_data = json.load(file)
            if not isinstance(json_data, list):
                raise ValueError(
                    f"file '{process_file}' has bad format expected list")
