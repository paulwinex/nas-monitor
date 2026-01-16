.PHONY: help deploy setup-remote setup-local remove-remote remove-local run dev-front sync

# Load .env file
include .env
export

help:
	@echo "NAS Monitor - Available Commands"
	@echo ""
	@echo "Deployment:"
	@echo "  make deploy         - Sync files to remote host and restart service"
	@echo "  make sync           - Sync files to remote host only (no restart)"
	@echo "  make setup-remote   - Setup systemd service on remote host"
	@echo "  make setup-local    - Setup systemd service on current host"
	@echo "  make remove-remote  - Remove service from remote host"
	@echo "  make remove-local   - Remove service from current host"
	@echo ""
	@echo "Running:"
	@echo "  make run            - Run in foreground mode (default)"
	@echo "  make run-remote     - Run on remote host in foreground (blocking terminal)"
	@echo "  make run-service    - Start as systemd service"
	@echo "  make stop           - Stop systemd service"
	@echo "  make restart        - Restart systemd service"
	@echo "  make status         - Show service status"
	@echo "  make logs           - Follow service logs"
	@echo ""
	@echo "Frontend:"
	@echo "  make dev-front      - Run frontend in dev mode"
	@echo ""
	@echo "Configuration:"
	@echo "  REMOTE_HOST=$(REMOTE_HOST)"
	@echo "  REMOTE_PATH=$(REMOTE_PATH)"

# Deployment commands
deploy:
	@./send.sh

sync:
	@echo "Syncing files to $(REMOTE_HOST):$(REMOTE_PATH)..."
	@rsync -av -P \
		--exclude='.venv' \
		--exclude='.idea' \
		--exclude='.git' \
		--exclude='uv.lock' \
		--exclude='front' \
		--exclude='_tmp' \
		--exclude='__pycache__' \
		--exclude='data' \
		--exclude='*.pyc' \
		. "$(REMOTE_HOST):$(REMOTE_PATH)/"
	@echo "Files synced successfully!"

setup-remote:
	@./setup-service.sh remote

setup-local:
	@./setup-service.sh local

remove-remote:
	@echo "Removing service from $(REMOTE_HOST)..."
	@ssh "$(REMOTE_HOST)" "systemctl stop nas-monitor 2>/dev/null || true"
	@ssh "$(REMOTE_HOST)" "systemctl disable nas-monitor 2>/dev/null || true"
	@ssh "$(REMOTE_HOST)" "rm -f /etc/systemd/system/nas-monitor.service"
	@ssh "$(REMOTE_HOST)" "systemctl daemon-reload"
	@echo "Service removed from remote host"

remove-local:
	@echo "Removing local service..."
	@sudo systemctl stop nas-monitor 2>/dev/null || true
	@sudo systemctl disable nas-monitor 2>/dev/null || true
	@sudo rm -f /etc/systemd/system/nas-monitor.service
	@sudo systemctl daemon-reload
	@echo "Service removed from local host"

# Running commands
run:
	@./run.sh foreground

run-remote:
	@echo "Running on remote host $(REMOTE_HOST) in foreground mode..."
	@echo "Press Ctrl+C to stop"
	@ssh -t "$(REMOTE_HOST)" "cd $(REMOTE_PATH) && ./run.sh foreground"

run-service:
	@./run.sh service

stop:
	@./run.sh stop

restart:
	@./run.sh restart

status:
	@./run.sh status

logs:
	@./run.sh logs

# Frontend
dev-front:
	@echo "Starting frontend in dev mode..."
	@cd front && quasar dev
