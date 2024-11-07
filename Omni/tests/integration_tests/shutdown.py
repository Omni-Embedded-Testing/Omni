from Omni.process_manager.process_manager import *
from Omni.applications.Openocd import *
from Omni.applications.Salea import *
from Omni.robotlibraries.gdb.gdb_control import *

current_file_path = os.path.abspath(__file__)
process_file = os.path.dirname(current_file_path)+"/Temp/my_process_cfg.json"
process_file = "/home/eks99th/Desktop/Omni/backend_processes_data.json"


close_applications(process_file)
