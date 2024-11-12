import json
import os
import subprocess
import psutil
from datetime import datetime
from pathlib import Path
from time import sleep



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


class ProcessManager:
    def __init__(self, _process_config_file):
        self.backend_config_file_path = _process_config_file
        self.backend_config_file_stream = self.load_config_file()
        self.backend_processes_data_file_name = self.fetch_backend_processes_data_file_name()
        self.backend_processes_data_path = Path(self.backend_config_file_path).parent / self.backend_processes_data_file_name
        self.backend_loaded_processes = None
        

    def load_config_file(self):
        with open(self.backend_config_file_path, 'r') as file:
            backend_config_file = json.load(file)
        return backend_config_file
    
    def fetch_backend_processes_data_file_name(self):
        backend_processes_data_file = self.backend_config_file_stream.get('backend_processes_data_file')
        if backend_processes_data_file is None:
            raise KeyError(f"The configuration file '{self.backend_config_file_path}' does not contain 'backend_processes_data_file' entry")
        return backend_processes_data_file

    def create_backend_processes_data_file(self, base_path=None):
        temp_backend_processes_data_path = self.__get_backend_processes_data_path(base_path)
        if self.check_file_exists(temp_backend_processes_data_path):
            self._error_msg_file_already_exists(temp_backend_processes_data_path)
        else:
            self.backend_processes_data_path=temp_backend_processes_data_path
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
            self.__terminate_process_by_pid(int(pid))
            application["status"] = "terminate requested"
            application["SIGTERM_time"] = datetime.now().strftime("%H:%M:%S.%f")[:-3],
        self.__save_processes_in_data_file(self.backend_loaded_processes)
            
    
    def verify_application_termination(self,kill_delay=1):
        for application in self.backend_loaded_processes:
            pid = application["pid"]
            print(f"Verifying application '{application['name']}' termination")
            try:
                process = psutil.Process(int(pid))
            except psutil.NoSuchProcess:
                print(f"Process '{application['name']}' with pid '{pid}' has been terminated successfully")
                application["status"] = "terminated"
                continue
            if process.is_running():
                print(f"Process '{application['name']}' with pid '{pid}' is still running. SIGTERM failed")
                print(f"Sending SIGKILL to process '{application['name']}' with pid '{pid}'")
                application["SIGKILL_time"] = datetime.now().strftime("%H:%M:%S.%f")[:-3],
                application["status"] = "SIGKILL requested"
                process.kill()
                sleep(kill_delay)
                try:
                    process = psutil.Process(int(pid))
                except psutil.NoSuchProcess:
                    print(f"Process '{application['name']}' with pid '{pid}' has been terminated after SIGKILL")
                    application["status"] = "killed"
                    continue
                if process.is_running():
                    print(f"Process '{application['name']}' with pid '{pid}' is still running. SIGKILL failed")
                    application["status"] = "SIGKILL failed"
        self.__save_processes_in_data_file(self.backend_loaded_processes)

    def __terminate_process_by_pid(self, pid: int):
        process = psutil.Process(pid)
        process.terminate()

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
