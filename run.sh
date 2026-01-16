#!/usr/bin/env bash

set -e

# Load .env file if exists
if [ -f .env ]; then
    export $(grep -v '^#' .env | xargs)
fi

MODE="${1:-foreground}"

case "$MODE" in
    foreground|fg)
        echo "Starting NAS Monitor in foreground mode..."
        export PYTHONPATH=${PWD}
        UV_BIN=$(command -v uv || which uv)
        if [ -z "$UV_BIN" ]; then
            for p in "/root/.local/bin/uv" "/usr/local/bin/uv" "/usr/bin/uv"; do
                if [ -x "$p" ]; then UV_BIN="$p"; break; fi
            done
        fi
        exec "${UV_BIN:-uv}" run nas_monitor
        ;;
    
    service)
        echo "Starting NAS Monitor as systemd service..."
        sudo systemctl start nas-monitor
        echo "Service started"
        sudo systemctl status nas-monitor --no-pager
        ;;
    
    stop)
        echo "Stopping NAS Monitor service..."
        sudo systemctl stop nas-monitor
        echo "Service stopped"
        ;;
    
    restart)
        echo "Restarting NAS Monitor service..."
        sudo systemctl restart nas-monitor
        echo "Service restarted"
        sudo systemctl status nas-monitor --no-pager
        ;;
    
    status)
        sudo systemctl status nas-monitor
        ;;
    
    logs)
        sudo journalctl -u nas-monitor -f
        ;;
    
    *)
        echo "Usage: $0 {foreground|fg|service|stop|restart|status|logs}"
        echo ""
        echo "Modes:"
        echo "  foreground, fg  - Run in foreground with output (default)"
        echo "  service         - Start as systemd service"
        echo "  stop            - Stop systemd service"
        echo "  restart         - Restart systemd service"
        echo "  status          - Show service status"
        echo "  logs            - Follow service logs"
        exit 1
        ;;
esac

