#!/bin/bash
set -e

# Define ANSI escape codes for text formatting
BOLD_BLUE='\e[1;34m'
BOLD_GREEN='\e[1;32m'
RESET='\e[0m'

echo -e "${BOLD_BLUE}Activating the Python virtual environment...${RESET}"
source venv/bin/activate

echo -e "${BOLD_BLUE}Running unit tests with pytest...${RESET}"
pytest ./tests/unit_tests/test_* -v --cov=./Omni --cov-report xml --cov-report html --cov-config=.coveragerc --junitxml=pytest.xml

echo -e "${BOLD_GREEN}Unit tests completed successfully.${RESET}"



