import shutil

import Omni.process_manager.process_manager as HostManager
import Omni.applications.Openocd as Openocd
import Omni.applications.Salea as SaleaBackend
from Omni.robotlibraries.gdb.gdb_control import *
import json
from time import sleep

current_file_path = os.path.abspath(__file__)
folder_path = os.path.dirname(current_file_path)+"/Temp"

# Function to extract each element's properties into a map with mandatory field check
def extract_backend_processes(process)->dict:
    mandatory_fields = ["name", "path", "arguments", "log_file"]
    # Check each field, and raise an error if it's missing
    for field in mandatory_fields:
        if field not in process or process[field] is None:
            raise ValueError(f"'{field}' is mandatory")
    return {
        "name": process.get("name"),
        "path": process.get("path"),
        "arguments": process.get("arguments"),
        "log_file": process.get("log_file")
    }



if not os.path.exists(folder_path):
    os.makedirs(folder_path)
else:
    shutil.rmtree(folder_path)
    os.makedirs(folder_path)

backend_processes_path = os.path.join(os.path.dirname(current_file_path), 'backend_processes_config.json')
with open(backend_processes_path, 'r') as file:
        backend_processes = json.load(file)
backend_processes_data_file = backend_processes.get('backend_processes_data_file')
if os.path.exists(backend_processes_data_file):
    os.remove(backend_processes_data_file)
HostManager.create_config_file(backend_processes_data_file)
backend_processes_array = backend_processes.get('backend_processes', [])
process_maped= extract_backend_processes(backend_processes_array[0])
log_file = process_maped["log_file"]
process_path = process_maped["path"]
process_arguments = process_maped["arguments"]
process_name = process_maped["name"]
Openocd.launch_openocd(backend_processes_data_file,process_path, process_arguments, log_file)
sleep(2)
Openocd.verify_openocd(backend_processes_data_file)


