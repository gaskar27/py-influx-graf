#!/bin/sh
set -e

touch /var/log/logger.log

exec "$@"
