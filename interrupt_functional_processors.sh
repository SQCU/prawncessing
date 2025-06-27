#!/bin/bash

PORTS=(5002 5003 5004 5005 5006)
LOG_FILE="impolite-shutdown-functional-processors.log"

# Combine lsof commands to get all PIDs at once
PIDS=$(lsof -t -i:5002 -i:5003 -i:5004 -i:5005 -i:5006)

if [ -z "$PIDS" ]; then
    echo "No functional processor servers found on ports 5002-5006."
    exit 0
fi

echo "Found the following functional processor server processes:"
# ps -p requires PIDs without leading/trailing whitespace and with commas as separators
ps -p $(echo $PIDS | tr ' ' ',')
echo ""

echo "Sending polite termination signal (SIGTERM)..."
kill $PIDS

echo "Waiting 1 second..."
sleep 1

# Check which processes are still alive
STUBBORN_PIDS=$(lsof -t -i:5002 -i:5003 -i:5004 -i:5005 -i:5006)

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
    echo "All functional processor servers shut down gracefully."
fi