#!/bin/bash

# Generic script to kill processes listening on specified ports.
# Usage: ./kill_ports.sh <port1> <port2> ...

PORTS=("$@")
LOG_FILE="impolite-shutdown-generic.log"

if [ ${#PORTS[@]} -eq 0 ]; then
    echo "Usage: ./kill_ports.sh <port1> <port2> ..."
    exit 1
fi

echo "Attempting to terminate processes on ports: ${PORTS[@]}"

# Build lsof command for all specified ports
LSOF_CMD=""
for PORT in "${PORTS[@]}"; do
    LSOF_CMD+=" -i:$PORT"
done

PIDS=$(lsof -t $LSOF_CMD)

if [ -z "$PIDS" ]; then
    echo "No processes found on the specified ports."
    exit 0
fi

echo "Found the following processes on the specified ports:"
ps -p $(echo $PIDS | tr ' ' ',')
echo ""

echo "Sending polite termination signal (SIGTERM)..."
kill $PIDS

echo "Waiting 2 seconds..."
sleep 2

# Check if processes are still alive
STUBBORN_PIDS=$(lsof -t $LSOF_CMD)

if [ -n "$STUBBORN_PIDS" ]; then
    echo "The following processes did not respond to SIGTERM:"
    ps -p $(echo $STUBBORN_PIDS | tr ' ' ',')
    
    echo "Logging impoliteness and sending SIGKILL..."
    {
        echo "---"
        echo "Timestamp: $(date)"
        echo "The following PIDs were forcefully terminated on ports ${PORTS[@]}:"
        ps -p $(echo $STUBBORN_PIDS | tr ' ' ',')
        echo "---"
    } >> "$LOG_FILE"
    
    kill -9 $STUBBORN_PIDS
    echo "Force kill signal sent."
else
    echo "All specified processes shut down gracefully."
fi
