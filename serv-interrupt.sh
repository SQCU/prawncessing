#!/bin/bash

PORTS=(8000 8001 8002)
LOG_FILE="impolite-shutdown.log"

# Combine lsof commands to get all PIDs at once
PIDS=$(lsof -t -i:8000 -i:8001 -i:8002)

if [ -z "$PIDS" ]; then
    echo "No servers found on ports 8000, 8001, or 8002."
    exit 0
fi

echo "Found the following server processes:"
# ps -p requires PIDs without leading/trailing whitespace and with commas as separators
ps -p $(echo $PIDS | tr ' ' ',')
echo ""

echo "Sending polite termination signal (SIGTERM)..."
kill $PIDS

echo "Waiting 1 second..."
sleep 1

# Check which processes are still alive
STUBBORN_PIDS=$(lsof -t -i:8000 -i:8001 -i:8002)

if [ -n "$STUBBORN_PIDS" ]; then
    echo "The following processes did not respond to SIGTERM:"
    ps -p $(echo $STUBBORN_PIDS | tr ' ' ',')
    
    echo "Logging impoliteness and sending SIGKILL..."
    {
        echo "---"
        echo "Timestamp: $(date)"
        echo "The following PIDs were forcefully terminated:"
        ps -p $(echo $STUBBORN_PIDS | tr ' ' ',')
        echo "---"
    } >> "$LOG_FILE"
    
    kill -9 $STUBBORN_PIDS
    echo "Force kill signal sent."
else
    echo "All servers shut down gracefully."
fi