#!/bin/bash
# This script adjusts the coverage report paths to ensure they are correctly recognized by SonarQube

# Define the original and replacement paths
original_path="<source>.*\/Omni\/Omni"
replacement_path="<source>/github/workspace/Omni"

# Adjust the paths in the coverage.xml file
sed -i "s|${original_path}</source>|${replacement_path}</source>|g" coverage.xml

echo "Coverage report paths have been adjusted for SonarQube."
