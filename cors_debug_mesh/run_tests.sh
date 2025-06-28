#!/bin/bash

# Set up logging
LOG_DIR="logs"
TIMESTAMP=$(date +"%Y%m%d_%H%M%S")
LOG_FILE="$LOG_DIR/run_tests_$TIMESTAMP.log"

# Ensure log directory exists
mkdir -p "$LOG_DIR"

# Group all commands and redirect their combined output to the log file.
{
    echo "Log file: $LOG_FILE"
    echo "---"

    # Activate the virtual environment
    echo "Activating virtual environment..."
    source ../.venv/bin/activate

    # Install test dependencies
    echo "Installing test dependencies..."
    uv pip install -r requirements-test.txt

    # Run pytest with a 60-second timeout to prevent hangs.
    echo "Running tests with a 60s timeout..."
    pytest --timeout=60

} >> "$LOG_FILE" 2>&1