#!/usr/bin/env bash

set -e

# Load .env file
if [ ! -f .env ]; then
    echo "Error: .env file not found"
    echo "Please create .env file with REMOTE_HOST and REMOTE_PATH"
    exit 1
fi

export $(grep -v '^#' .env | grep -E '^(REMOTE_HOST|REMOTE_PATH)=' | xargs)

if [ -z "$REMOTE_HOST" ] || [ -z "$REMOTE_PATH" ]; then
    echo "Error: REMOTE_HOST and REMOTE_PATH must be set in .env"
    exit 1
fi

echo "Syncing files to $REMOTE_HOST:$REMOTE_PATH..."

rsync -av -P \
  --exclude='.venv' \
  --exclude='.idea' \
  --exclude='.git' \
  --exclude='uv.lock' \
  --exclude='front' \
  --exclude='_tmp' \
  --exclude='__pycache__' \
  --exclude='data' \
  --exclude='*.pyc' \
  . "$REMOTE_HOST:$REMOTE_PATH/"

echo "Files synced successfully!"

echo "Installing dependencies on remote host..."
ssh "$REMOTE_HOST" "cd $REMOTE_PATH && uv sync"

echo "Restarting service..."
ssh "$REMOTE_HOST" "systemctl restart nas-monitor 2>/dev/null || echo 'Service not configured, skipping restart'"

echo "Deployment complete!"

