#!/bin/bash
# This script safely and completely shuts down the dct_refurb service.

# Find the PID of the main orchestrator script
MAIN_PID=$(pgrep -f "python -u -m main")

if [ -z "$MAIN_PID" ]; then
    echo "dct_refurb service not found."
    exit 0
fi

# There might be multiple PIDs if something went wrong.
# We'll find the process group ID (PGID) from the first one.
# In a shell, the PGID of a process is the same as its PID if it's a group leader.
# When we use `kill`, we target the negative of the PGID to kill the whole group.
PGID=$(ps -o pgid= $MAIN_PID | grep -o '[0-9]*')

if [ -z "$PGID" ]; then
    echo "Could not determine Process Group ID for PID $MAIN_PID. Killing PID directly."
    kill -9 $MAIN_PID
else
    echo "Found dct_refurb service running with Process Group ID: $PGID. Terminating group."
    # Kill the entire process group
    kill -9 -- -$PGID
fi

sleep 1
echo "Shutdown complete."
