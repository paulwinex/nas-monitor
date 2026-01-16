#!/usr/bin/env bash

set -e

# Load .env file
if [ -f .env ]; then
    export $(grep -v '^#' .env | grep -E '^(REMOTE_HOST|REMOTE_PATH)=' | xargs)
fi

MODE="${1:-remote}"

if [ "$MODE" = "local" ]; then
    echo "Removing local service..."
    sudo systemctl stop nas-monitor 2>/dev/null || true
    sudo systemctl disable nas-monitor 2>/dev/null || true
    sudo rm -f /etc/systemd/system/nas-monitor.service
    sudo systemctl daemon-reload
    echo "Service removed from local host"
    
elif [ "$MODE" = "remote" ]; then
    if [ -z "$REMOTE_HOST" ] || [ -z "$REMOTE_PATH" ]; then
        echo "Error: REMOTE_HOST and REMOTE_PATH must be set in .env"
        exit 1
    fi
    
    echo "Removing service from $REMOTE_HOST..."
    ssh "$REMOTE_HOST" << 'EOF'
systemctl stop nas-monitor 2>/dev/null || true
systemctl disable nas-monitor 2>/dev/null || true
rm -f /etc/systemd/system/nas-monitor.service
systemctl daemon-reload
EOF
    echo "Service removed from remote host"
    
else
    echo "Usage: $0 {local|remote}"
    echo ""
    echo "  local  - Remove service from current host"
    echo "  remote - Remove service from remote host (from .env)"
    exit 1
fi
