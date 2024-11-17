#!/bin/bash
set -e

# ANSI escape codes for bold blue text
BLUE_BOLD='\e[1;34m'
# ANSI escape codes for bold green text
GREEN_BOLD='\e[1;32m'
# ANSI escape code to reset text formatting
RESET='\e[0m'

echo -e "${BLUE_BOLD}Activating the Python virtual environment...${RESET}"
source venv/bin/activate

echo -e "${BLUE_BOLD}Starting host applications...${RESET}"
omni-backend-start --backend ./integration_tests/backend_processes_config.json -l ./integration_tests/Temp/ --overwrite --port-delay 10




