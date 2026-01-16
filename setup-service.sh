#!/usr/bin/env bash

set -e

# Load .env file
if [ -f .env ]; then
    export $(grep -v '^#' .env | grep -E '^(REMOTE_HOST|REMOTE_PATH)=' | xargs)
fi

MODE="${1:-remote}"

if [ "$MODE" = "local" ]; then
    echo "🔧 Setting up NAS Monitor service locally..."
    
    sudo cp nas-monitor.service /etc/systemd/system/
    sudo systemctl daemon-reload
    sudo systemctl enable nas-monitor
    sudo systemctl restart nas-monitor
    sudo systemctl status nas-monitor --no-pager
    
    echo "Local service setup complete!"
    echo "Check logs with: sudo journalctl -u nas-monitor -f"
    
elif [ "$MODE" = "remote" ]; then
    if [ -z "$REMOTE_HOST" ] || [ -z "$REMOTE_PATH" ]; then
        echo "Error: REMOTE_HOST and REMOTE_PATH must be set in .env"
        exit 1
    fi
    
    echo "🔧 Setting up NAS Monitor service on $REMOTE_HOST..."
    
    # Copy service file
    echo "Copying service file..."
    scp nas-monitor.service "$REMOTE_HOST:/etc/systemd/system/"
    
    # Enable and start service
    echo "Enabling and starting service..."
    ssh "$REMOTE_HOST" << 'EOF'
systemctl daemon-reload
systemctl enable nas-monitor
systemctl restart nas-monitor
systemctl status nas-monitor --no-pager
EOF
    
    echo "Remote service setup complete!"
    echo "Check logs with: ssh $REMOTE_HOST journalctl -u nas-monitor -f"
    
else
    echo "Usage: $0 {local|remote}"
    echo ""
    echo "  local  - Setup service on current host"
    echo "  remote - Setup service on remote host (from .env)"
    exit 1
fi
