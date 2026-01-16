import logging
import psutil
import time
from datetime import datetime, timedelta, timezone

from tortoise import Tortoise, transactions

from nas_monitor.models import Device, RawMetric, DailyMetric, HistoryMetric, MigrationState
from nas_monitor.shemas import Metrics


async def get_all_devices():
    return await Device.all()


async def get_enabled_devices_by_type(dev_type: str):
    return await Device.filter(enabled=True, type=dev_type).all()

# todo: from config
# data compression time ranges
RETENTION = {
    "raw": timedelta(hours=3),
    "daily": timedelta(days=7),
    "history": timedelta(days=365)
}

# map type to model
MODELS_MAP = {
    "raw": RawMetric,
    "daily": DailyMetric,
    "history": HistoryMetric
}


async def upsert_device(name: str, dev_type: str = "unknown", details: dict|None = None):
    """
    Create or update device
    """
    device, created = await Device.update_or_create(
        name=name,
        defaults={
            "type": dev_type,
            "details": details
        }
    )
    return device


async def add_metrics_batch(data: list[Metrics]):
    devices = await Device.all()
    device_map = {d.name: d for d in devices}

    to_create = []
    now = datetime.now(timezone.utc)

    for item in data:
        # get device
        device = device_map.get(item.device_name)

        if not device:
            print(f"Warning: Device {item.device_name} not found in database. Run inventory.")
            continue
        to_create.append(RawMetric(
            timestamp=now,
            device=device,
            label=item.label,
            value=item.value
        ))

    if to_create:
        await RawMetric.bulk_create(to_create)
        logging.debug('Added metrics batch %s', len(to_create))


async def run_aggregation(source_model, target_model, stage_name: str, interval_minutes: int):
    logging.debug('Running aggregation on %s', stage_name)
    state, _ = await MigrationState.get_or_create(stage=stage_name)

    last_entry = await source_model.all().order_by("-timestamp").first()
    if not last_entry: return

    cutoff_time = last_entry.timestamp.replace(second=0, microsecond=0)
    if interval_minutes >= 60:
        cutoff_time = cutoff_time.replace(minute=0)

    table_name = source_model._meta.db_table
    interval_sec = interval_minutes * 60

    # group by interval, device and label
    query = f"""
        SELECT 
            (CAST(strftime('%s', timestamp) AS INT) / {interval_sec}) * {interval_sec} as interval_ts,
            device_id,
            label, 
            AVG(value) as avg_val,
            MAX(id) as max_id
        FROM {table_name}
        WHERE id > {state.last_processed_id} AND timestamp < '{cutoff_time.isoformat()}'
        GROUP BY interval_ts, device_id, label
        ORDER BY interval_ts ASC
    """

    conn = Tortoise.get_connection("default")
    results = await conn.execute_query_dict(query)

    if results:
        async with transactions.in_transaction():
            new_entries = [
                target_model(
                    timestamp=datetime.fromtimestamp(row['interval_ts'], tz=timezone.utc),
                    device_id=row['device_id'],
                    label=row['label'],
                    value=row['avg_val']
                ) for row in results
            ]
            await target_model.bulk_create(new_entries)
            state.last_processed_id = max(row['max_id'] for row in results)
            await state.save()


async def cleanup_metrics():
    logging.debug('Cleaning up metrics')
    now = datetime.now(timezone.utc)
    for key, model in [("raw", RawMetric), ("daily", DailyMetric), ("history", HistoryMetric)]:
        await model.filter(timestamp__lt=now - RETENTION[key]).delete()


async def _read_range(model, devices: list[str] = None, labels: list[str] = None,
                      from_date: datetime = None, to_date: datetime = None):
    queryset = model.all()
    if devices:
        queryset = queryset.filter(device__name__in=devices)
    if labels:
        queryset = queryset.filter(label__in=labels)
    if from_date:
        queryset = queryset.filter(timestamp__gte=from_date)
    if to_date:
        queryset = queryset.filter(timestamp__lte=to_date)
    return await queryset.order_by("timestamp").values(
        "timestamp",
        "label",
        "value",
        device_name="device__name"
    )

async def read_raw_range(devices=None, labels=None, start=None, end=None):
    return await _read_range(RawMetric, devices, labels, start, end)

async def read_daily_range(devices=None, labels=None, start=None, end=None):
    return await _read_range(DailyMetric, devices, labels, start, end)

async def read_history_range(devices=None, labels=None, start=None, end=None):
    return await _read_range(HistoryMetric, devices, labels, start, end)



async def fetch_metrics_data(
        history_type: str,
        device_types: list[str] = None,
        start_time: datetime = None,
        end_time: datetime = None
    ) -> list[dict]:
    model = MODELS_MAP.get(history_type)
    if not model:
        raise ValueError(f"Invalid history type: {history_type}")
    queryset = model.all()
    if device_types:
        queryset = queryset.filter(device__type__in=device_types)
    if start_time:
        queryset = queryset.filter(timestamp__gte=start_time)
    if end_time:
        queryset = queryset.filter(timestamp__lte=end_time)
    return await queryset.order_by("timestamp").values(
        "id",
        "timestamp",
        "label",
        "value",
        device_name="device__name",
        device_type="device__type"
    )


async def get_latest_metrics_by_device(device_types: list[str] = None) -> dict:
    """
    Get latest metric value for each device/label combination.
    Returns dict: {device_name: {label: value}}
    """
    queryset = RawMetric.all()
    if device_types:
        queryset = queryset.filter(device__type__in=device_types)
    
    # Get latest metrics grouped by device and label
    results = await queryset.order_by("-timestamp").values(
        "timestamp",
        "label",
        "value",
        device_name="device__name"
    )
    
    # Group by device and label, keeping only the latest
    latest = {}
    seen = set()
    
    for row in results:
        key = (row['device_name'], row['label'])
        if key not in seen:
            seen.add(key)
            if row['device_name'] not in latest:
                latest[row['device_name']] = {}
            latest[row['device_name']][row['label']] = row['value']
    
    return latest


async def get_inventory_grouped() -> dict:
    """
    Get devices grouped by ZFS pools and standalone devices.
    Returns:
    {
        "uptime_seconds": 12345,
        "zpools": [...],
        "system_devices": {...}
    }
    """
    all_devices = await Device.all()
    uptime = int(time.time() - psutil.boot_time())
    
    # Get ZFS pools
    zpools = [d for d in all_devices if d.type == "zfs_pool"]
    
    # Get storage devices
    storage_devices = [d for d in all_devices if d.type == "storage"]
    
    # Map storage devices to their pools
    storage_by_pool = {}
    standalone_storage = []
    
    for disk in storage_devices:
        pool_name = disk.details.get("zfs_pool") if disk.details else None
        if pool_name:
            if pool_name not in storage_by_pool:
                storage_by_pool[pool_name] = []
            storage_by_pool[pool_name].append({
                "name": disk.name,
                "type": disk.type,
                "enabled": disk.enabled,
                "details": disk.details
            })
        else:
            standalone_storage.append({
                "name": disk.name,
                "type": disk.type,
                "enabled": disk.enabled,
                "details": disk.details
            })
    
    # Build zpool groups (only pools with >1 disk)
    zpool_groups = []
    for pool in zpools:
        pool_disks = storage_by_pool.get(pool.name, [])
        if len(pool_disks) > 1:
            zpool_groups.append({
                "name": pool.name,
                "type": pool.type,
                "enabled": pool.enabled,
                "details": pool.details,
                "disks": pool_disks
            })
        elif len(pool_disks) == 1:
            # Single disk pool goes to standalone
            standalone_storage.extend(pool_disks)
    
    # Get system devices
    cpu = next((d for d in all_devices if d.type == "cpu"), None)
    ram = next((d for d in all_devices if d.type == "ram"), None)
    network = next((d for d in all_devices if d.type == "network"), None)
    
    return {
        "uptime_seconds": uptime,
        "zpools": zpool_groups,
        "system_devices": {
            "cpu": {
                "name": cpu.name,
                "type": cpu.type,
                "enabled": cpu.enabled,
                "details": cpu.details
            } if cpu else None,
            "ram": {
                "name": ram.name,
                "type": ram.type,
                "enabled": ram.enabled,
                "details": ram.details
            } if ram else None,
            "network": {
                "name": network.name,
                "type": network.type,
                "enabled": network.enabled,
                "details": network.details
            } if network else None,
            "storage": standalone_storage
        }
    }