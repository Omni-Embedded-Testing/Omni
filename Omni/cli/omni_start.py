import argparse
import Omni.process_manager.process_manager 

def main():
    parser = argparse.ArgumentParser(description="Starts the backend processes according to the provided configuration.")
    
    # Define CLI arguments
    parser.add_argument("-b", "--backend", 
                        help="Path to the configuration file for backend processes (required). This file specifies the processes to start.",
                        type=str, 
                        required=True)
    parser.add_argument("-l", "--log-folder", 
                        help="Path to the folder where logs will be saved. If not provided, logs will be saved in the same directory as the configuration file.",
                        type=str)
    
    args = parser.parse_args()

    process_manager = Omni.process_manager.process_manager.ProcessManager(args.backend)
    if args.log_folder:
        process_manager.create_backend_processes_data_file(args.log_folder)
    else:
        process_manager.create_backend_processes_data_file()
    process_manager.launch_processes()