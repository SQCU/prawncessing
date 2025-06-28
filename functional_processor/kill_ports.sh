#!/bin/bash
for port in "$@"
do
    echo "Killing process on port $port"
    lsof -ti:$port | xargs kill -9
done
