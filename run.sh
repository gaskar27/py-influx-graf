#!/usr/bin/env bash

set -euo pipefail

mkdir -p ~/.influxdb3/data ~/.influxdb3/plugins

docker compose up -d
