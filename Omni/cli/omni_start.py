import argparse
import Omni.process_manager.process_manager
from time import sleep
from Omni.cli.console_animations import sleep_with_progress
from rich.console import Console

NO_ERROR = 0
ERROR = -1


def main():
    console = Console()
    parser = argparse.ArgumentParser(description="Starts the backend processes according to the provided configuration.")
    parser.add_argument("-b", "--backend", 
                        help="Path to the configuration file for backend processes (required). This file specifies the processes to start.",
                        type=str, 
                        required=True)
    parser.add_argument("-l", "--log-folder", 
                        help="Path to the folder where logs will be saved. If not provided, logs will be saved in the same directory as the configuration file.",
                        type=str, default=None)
    parser.add_argument("-o", "--overwrite", 
                        help="Flag to indicate whether to overwrite the existing backend processes data file.",
                        action="store_true")
    parser.add_argument("-pd", "--port-delay", 
                        help="Delay in seconds before checking if all process ports are open.",
                        type=int, 
                        default=5)
    parser.add_argument("-td", "--termination-delay", 
                        help="Delay in seconds before verifying all processes stoped in case of a failure.",
                        type=int, 
                        default=10)
    args = parser.parse_args()

    process_manager = Omni.process_manager.process_manager.ProcessManager(args.backend)
    process_manager.create_backend_processes_data_file(args.log_folder, args.overwrite)
    process_manager.launch_processes()
    console.print("[green]All processes have been started successfully.[/green]", style="bold green")
    console.print("[yellow]Verifying if the ports are open.[/yellow]", style="bold yellow")
    try:
        sleep_with_progress(args.port_delay, "Port Start-up time")
        process_manager.verify_open_ports()        
    except Omni.process_manager.process_manager.PortClosedError as e:
        console.print(f"[bold red]An error occurred: {e}[/bold red]")
        console.print("[bold red]Stopping all started backend processes.[/bold red]")
        process_manager.load_backend_processes_data_file(args.log_folder)
        process_manager.close_applications()
        sleep_with_progress(args.termination_delay, "Process Termination time")
        process_manager.verify_application_termination(args.termination_delay)
        return ERROR
    console.print("[green]Host applications successfully started.[/green]", style="bold green")
    return NO_ERROR