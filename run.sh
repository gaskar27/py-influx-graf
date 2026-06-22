#!/usr/bin/env sh

set -e

if [ -z $1 ]; then
    echo "Usage: $0 <args>"
    echo "args:"
    echo "      start : Run the application"
    echo "      stop  : Stop the application"
    echo "      down  : Stop the application and remove data"
    exit 1
fi

if [ "$1" = "down" ]; then
    docker compose down -v

    if [ -d ~/.influxdb3/data ]; then
        rm -rf ~/.influxdb3/data
    fi

    exit 0
fi

if [ "$1" = "stop" ]; then
    docker compose stop
    exit 0
fi

if [ "$1" = "start" ]; then
    mkdir -p ~/.influxdb3/data
    docker compose up -d
    exit 0
fi
