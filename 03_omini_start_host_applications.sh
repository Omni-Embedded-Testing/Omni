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
python3 ./Omni/tests/integration_tests/startup.py

echo -e "${GREEN_BOLD}Host applications successfully started.${RESET}"




