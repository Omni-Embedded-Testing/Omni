import argparse
from time import sleep
import Omni.process_manager.process_manager 


def main():
    parser = argparse.ArgumentParser(description="Omni Stop command-line interface.")
    parser.add_argument("-b", "--backend", 
                        help="Path to the configuration file for backend processes (required). This file specifies the processes to start.",
                        type=str, 
                        required=True)
    parser.add_argument("-p", "--process-data", 
                        help="Path to the folder where process data is located. If not provided, the same directory as the configuration file will be assumed.",
                        type=str)
    parser.add_argument("-d", "--delay", 
                        help="Delay in seconds before verifying if the processes are terminated.",
                        type=int, 
                        default=1)
    args = parser.parse_args()
    process_stoper = Omni.process_manager.process_manager.ProcessManager(args.backend)
    if args.process_data:
        process_stoper.load_backend_processes_data_file(args.process_data)
    else:
        process_stoper.load_backend_processes_data_file()
    process_stoper.close_applications()
    sleep(args.delay)
    process_stoper.verify_application_termination(args.delay)
    print("All processes have been terminated successfully.")
