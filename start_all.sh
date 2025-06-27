#!/bin/bash

echo "Interrupting any running services..."
./interrupt_functional_processors.sh
./kill_ports.sh 5007 8003 5008

echo "Starting all services..."

echo "Starting visualizer services..."
./start_visualizer_services.sh

echo "Starting functional processor services..."
./functional_processor/start_functional_processors.sh

echo "All services started."