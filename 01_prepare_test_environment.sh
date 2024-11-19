#!/bin/bash

# ANSI escape codes for bold blue text
BLUE_BOLD='\e[1;34m'
# ANSI escape codes for bold green text
GREEN_BOLD='\e[1;32m'
# ANSI escape code to reset text formatting
RESET='\e[0m'

venv_name="venv"

echo -e "${BLUE_BOLD}Creating a Python virtual environment named '$venv_name'...${RESET}"
python3 -m venv $venv_name

echo -e "${BLUE_BOLD}Activating the virtual environment '$venv_name'...${RESET}"
source $venv_name/bin/activate

echo -e "${BLUE_BOLD}Installing required packages using pip...${RESET}"
pip install -r Omni/requirements.txt

echo -e "${BLUE_BOLD}Installing Omni in the virtual environment...${RESET}"
pip install -e .

echo -e "${GREEN_BOLD}Test Environment set-up complete.${RESET}"



