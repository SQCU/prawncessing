#!/bin/bash

# Start the save server in the background
python3 save_server.py &
SAVE_SERVER_PID=$!

# Start the app server in the background
python3 app_server.py &
APP_SERVER_PID=$!

# Start the proxy server in the foreground
python3 proxy_server.py

# Clean up background processes on exit
trap "kill $SAVE_SERVER_PID $APP_SERVER_PID" EXIT
# To stop these services, you can also use `kill_ports.sh` with their respective ports if they become hung.
