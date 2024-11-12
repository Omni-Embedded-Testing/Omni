import shutil
import os
import Omni.process_manager.process_manager 

from time import sleep

current_file_path = os.path.abspath(__file__)
temp_folder_path = os.path.dirname(current_file_path)+"/Temp"

if not os.path.exists(temp_folder_path):
    os.makedirs(temp_folder_path)
else:
    shutil.rmtree(temp_folder_path)
    os.makedirs(temp_folder_path)

backend_processes_path = os.path.join(os.path.dirname(current_file_path), 'backend_processes_config.json')
process_manager = Omni.process_manager.process_manager.ProcessManager(backend_processes_path)
process_manager.create_backend_processes_data_file(temp_folder_path)
process_manager.launch_processes()



