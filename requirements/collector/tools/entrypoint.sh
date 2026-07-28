#!/bin/sh
set -e

touch /var/log/logger.log

ln -s /usr/local/bin/tools/all.sh /usr/local/bin/all
ln -s /usr/local/bin/tools/aria.sh /usr/local/bin/aria
ln -s /usr/local/bin/tools/powerstore.sh /usr/local/bin/powerstore
ln -s /usr/local/bin/tools/unity.sh /usr/local/bin/unity
ln -s /usr/local/bin/tools/vsphere.sh /usr/local/bin/vsphere

exec "$@"
