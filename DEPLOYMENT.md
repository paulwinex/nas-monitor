# Smart Monitor - Deployment Guide

## Backend Deployment

### First Time Setup

1. **Deploy files to remote host:**
   ```bash
   ./send.sh
   ```

2. **Setup systemd service:**
   ```bash
   ./setup-service.sh
   ```

3. **Check service status:**
   ```bash
   ssh root@192.168.0.10 systemctl status nas-monitor
   ```

### Subsequent Deployments

Just run the deploy script:
```bash
./send.sh
```

This will:
- Sync files to `/opt/nas_monitor` on remote host
- Install dependencies with `uv sync`
- Restart the service automatically

### Logs

View logs on remote host:
```bash
ssh root@192.168.0.10 journalctl -u nas-monitor -f
```

## Frontend Development

### Local Development

1. **Configure API endpoint:**
   Edit `front/.env`:
   ```
   VITE_API_BASE=http://192.168.0.10:8000
   ```

2. **Install dependencies:**
   ```bash
   cd front
   npm install
   ```

3. **Run dev server:**
   ```bash
   npm run dev
   ```

Frontend will be available at `http://localhost:9000`

### Production Build

```bash
cd front
npm run build
```

Build output will be in `front/dist/spa`

## Configuration

### Backend Configuration

Environment variables (prefix: `NAS_`):
- `NAS_DB_PATH` - Database path (default: `sqlite://data/metrics_db.sqlite3`)
- `NAS_COLLECTOR_INTERVAL_CPU` - CPU polling interval in seconds (default: 5)
- `NAS_COLLECTOR_INTERVAL_RAM` - RAM polling interval in seconds (default: 5)
- `NAS_COLLECTOR_INTERVAL_NETWORK` - Network polling interval in seconds (default: 3)
- `NAS_COLLECTOR_INTERVAL_STORAGE` - Storage polling interval in seconds (default: 60)
- `NAS_COLLECTOR_INTERVAL_ZFS_POOL` - ZFS pool polling interval in seconds (default: 600)
- `NAS_DISABLE_TASKS` - Disable background tasks (default: false)

Create `.env` file in project root to override defaults.

### Frontend Configuration

Environment variables (prefix: `FRONTEND_`):
- `FRONTEND_UPDATE_INTERVALS` - JSON object with update intervals
- `FRONTEND_CHART_HISTORY_POINTS` - Number of points in charts (default: 40)
- `FRONTEND_RAW_METRICS_HOURS` - Hours of raw metrics to fetch (default: 1)
