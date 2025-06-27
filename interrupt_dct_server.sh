#!/bin/bash

# This script specifically targets the DCT server.
# Note: For a more generic solution, consider using `kill_ports.sh` with the relevant port.
PORT=5002
LOG_FILE="impolite-shutdown-dct-server.log"

# Get PID of process using the specific port
PIDS=$(lsof -t -i:$PORT)

if [ -z "$PIDS" ]; then
    echo "No server found on port $PORT."
    exit 0
fi

echo "Found the following server processes on port $PORT:"
ps -p $(echo $PIDS | tr ' ' ',')
echo ""

echo "Sending polite termination signal (SIGTERM)..."
kill $PIDS

echo "Waiting 1 second..."
sleep 1

# Check if processes are still alive
STUBBORN_PIDS=$(lsof -t -i:$PORT)

if [ -n "$STUBBORN_PIDS" ]; then
    echo "The following processes did not respond to SIGTERM:"
    ps -p $(echo $STUBBORN_PIDS | tr ' ' ',')
    
    echo "Logging impoliteness and sending SIGKILL..."
    {
        echo "---"
        echo "Timestamp: $(date)"
        echo "The following PIDs were forcefully terminated on port $PORT:"
        ps -p $(echo $STUBBORN_PIDS | tr ' ' ',')
        echo "---"
    } >> "$LOG_FILE"
    
    kill -9 $STUBBORN_PIDS
    echo "Force kill signal sent."
else
    echo "Server on port $PORT shut down gracefully."
fi