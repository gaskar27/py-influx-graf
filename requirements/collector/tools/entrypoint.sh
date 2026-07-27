#!/bin/sh
set -e

touch /var/log/logger.log

cd /usr/local/bin/tools/

ln -s all.sh /usr/local/bin/all
ln -s aria.sh /usr/local/bin/aria
ln -s powerstore.sh /usr/local/bin/powerstore
ln -s unity.sh /usr/local/bin/unity
ln -s vsphere.sh /usr/local/bin/vsphere

cd -

exec "$@"
