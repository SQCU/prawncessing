#!/bin/bash

# This script interrupts all services, including the functional
# processors and the proxy server.

cd "$(dirname "$0")"

echo "Interrupting functional processors..."
./functional_processor/interrupt_functional_processors.sh

echo "Interrupting proxy server..."
kill $(lsof -t -i:5008) 2>/dev/null || echo "Proxy server not running."

echo "All services interrupted."
