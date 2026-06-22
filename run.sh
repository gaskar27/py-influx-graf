#!/usr/bin/env sh

set -e

if [ -z "$1" ]; then
    echo "Usage: $0 <args>"
    echo "args:"
    echo "      start : Run the application"
    echo "      stop  : Stop the application"
    echo "      down  : Stop the application and remove data"
    exit 1
fi

case "$1" in
    "start" | "s")
        docker compose up -d
        ;;

    "stop" | "st")
        docker compose stop
        ;;

    "down" | "d")
        docker compose down -v
        ;;

    *)
        echo "Usage: $0 <args>"
        echo "args:"
        echo "      start : Run the application"
        echo "      stop  : Stop the application"
        echo "      down  : Stop the application and remove data"
        exit 1
        ;;
esac
