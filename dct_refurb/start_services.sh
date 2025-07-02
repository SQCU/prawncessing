#!/bin/bash

# Get the directory of this script
SCRIPT_DIR=$( cd -- "$( dirname -- "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )
cd "$SCRIPT_DIR" || exit

# This script automates the process of stopping, updating, and restarting the dct_refurb service.

# Step 1: Kill any existing services
echo "--- Stopping any existing dct_refurb services... ---"
bash ./interrupt_services.sh
# Add a small delay to allow processes to terminate gracefully.
sleep 2

# Step 2: Install/update dependencies
echo "--- Installing/updating dependencies... ---"
# Activate the virtual environment, which is in the parent directory
source ../.venv/bin/activate
if [ $? -ne 0 ]; then
    echo "ERROR: Failed to activate virtual environment. Aborting."
    exit 1
fi
# Install dependencies using uv
uv pip install -r requirements.txt
if [ $? -ne 0 ]; then
    echo "ERROR: Failed to install dependencies. Aborting."
    exit 1
fi

# Step 3: Start the service in the background
echo "--- Starting the dct_refurb service in the background... ---"
# Clear the old log file before starting
> service.log
# Run the main script with nohup to detach it from the terminal
# and redirect all output to the log file.
nohup python -u -m main >> service.log 2>&1 &
# Add a small delay to allow the services to initialize.
sleep 3

# Step 4: Inform the user
echo "--- Service started successfully! ---"
echo
echo "The web interface should be available at:"
echo "  => http://127.0.0.1:8000"
echo
echo "You can monitor the service logs with the command:"
echo "  tail -f service.log"
echo