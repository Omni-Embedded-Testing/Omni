import argparse
import Omni.process_manager.process_manager 

def main():
    parser = argparse.ArgumentParser(description="Omni Stop command-line interface.")
    
    # Define CLI arguments
    parser.add_argument("-p", "--parameter", help="Example parameter for Omni", type=str)
    parser.add_argument("-v", "--verbose", action="store_true", help="Enable verbose output")
    backend= "/home/eks99th/Desktop/Omni/integration_tests/backend_processes_config.json"
    process_manager = Omni.process_manager.process_manager.ProcessManager(backend)
