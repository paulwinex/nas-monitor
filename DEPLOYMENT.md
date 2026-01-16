# Smart Monitor - Deployment Guide

This project is designed to run the backend on "bare metal" (to have direct access to hardware sensors and ZFS) and the frontend as a static build or a Docker container.

All management is handled via the root `Makefile`.

## Initial Setup

1. **Configure Environment:**
   Create a `.env` file in the project root:
   ```bash
   REMOTE_HOST=root@your-nas-ip
   REMOTE_PATH=/opt/nas_monitor
   ```

2. **Setup Remote Service:**
   This command installs the `systemd` service on the target host.
   ```bash
   make setup-remote
   ```

## Backend Management

### Deployment
Sync files, install dependencies on the host, and restart the service:
```bash
make deploy
```

### Logs
Watch live logs from the remote host:
```bash
make logs-remote
```

### Service Control
- `make setup-remote` / `make remove-remote`
- `make setup-local` / `make remove-local`
- `make start` / `make stop` / `make restart`
- `make status`

## Project Structure
- `run.sh`: Main entrypoint for the application.
- `send.sh`: Deployment script.
- `scripts/`: Auxiliary setup and service management scripts.
- `front/`: Frontend source and Docker configuration.

The frontend can be run locally for development or built as a Docker image for production sharing.

### Development Mode
Runs the Quasar dev server (requires Node.js and Quasar CLI):
```bash
make dev-front
```

### Production Docker Build
Builds a multi-stage Docker image that serves the static SPA using Nginx:
```bash
make docker-build-front
```
The resulting image is tagged as `nas-monitor-front`.

## Hardware Requirements
The backend requires:
- `smartmontools` (for disk temperatures and health)
- `zfsutils-linux` (if monitoring ZFS pools)
- Python 3.10+
- `uv` (Fast Python package manager)
