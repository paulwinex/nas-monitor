# NAS Monitor

A real-time monitoring dashboard designed for NAS (Network Attached Storage) and server environments. It provides basic visibility into system health, storage performance, and host management.

![Dashboard Preview](images/screen1.png)

## Key Features

- **Real-time Metrics**: Live tracking of CPU load, RAM usage, and Network throughput.
- **ZFS Integration**: Comprehensive monitoring of ZFS pools, including health status and occupancy.
- **Disk Health**: SMART monitoring for temperatures and basic disk parameters for both NVMe and SATA drives.
- **Historical Data**: Aggregated history with support for up to 10 years of data retention.
- **Host Management**: Direct system controls for Restarting and Powering Off the host with safety confirmations.
- **Panel Customization**: Quick visibility toggles to hide/show specific devices on the dashboard.
- **System Info**: Instant access to OS details, kernel version, and hardware architecture.

## Tech Stack

- **Backend**: Python 3.10+ (FastAPI, Tortoise ORM, psutil)
- **Frontend**: Vue.js 3, Quasar Framework, Pinia, ApexCharts
- **Storage**: SQLite for metrics and configuration.

## Getting Started

To install and deploy the monitor, please refer to the detailed **[Deployment Guide](DEPLOYMENT.md)**.

### Quick Start (Local Development)

```bash
# Start backend
make run

# Start frontend (separate shell)
make dev-front
```

## License
MIT
