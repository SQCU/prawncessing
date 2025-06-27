#!/bin/bash

PORTS=(3000 8001 8002 8003)

echo "Checking for hung processes on ports: ${PORTS[@]}"
echo "--------------------------------------------------"

for PORT in "${PORTS[@]}"; do
    echo "Checking port $PORT..."
    # Use lsof to find processes listening on the port
    # -t: only print process IDs
    # -i :<port>: list network files by Internet address (port)
    PIDS=$(lsof -t -i :$PORT)

    if [ -n "$PIDS" ]; then
        echo "  Found hung process(es) on port $PORT with PID(s): $PIDS"
        echo "  You may want to kill these processes, e.g., 'kill -9 $PIDS'"
    else
        echo "  No hung processes found on port $PORT."
    fi
    echo ""
done

echo "--------------------------------------------------"
echo "Check complete."
