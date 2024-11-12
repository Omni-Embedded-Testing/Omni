from Omni.process_manager.process_manager import *
# from Omni.applications.Openocd import *
# from Omni.applications.Salea import *
# from Omni.robotlibraries.gdb.gdb_control import *


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

current_file_path = os.path.abspath(__file__)
backend_processes_path = os.path.join(os.path.dirname(current_file_path), 'backend_processes_config.json')
with open(backend_processes_path, 'r') as file:
        backend_processes = json.load(file)
backend_processes_array = backend_processes.get('backend_processes', [])
process_maped= extract_backend_processes(backend_processes_array[0])
close_applications(process_maped)
