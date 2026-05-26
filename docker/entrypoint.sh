#!/bin/bash
PUID=${PUID:-99}
PGID=${PGID:-100}

echo "Starting MetaDen with UID=${PUID} GID=${PGID}"

mkdir -p /config
chown -R ${PUID}:${PGID} /config 2>/dev/null || true

exec /usr/bin/supervisord -c /etc/supervisor/supervisord.conf
