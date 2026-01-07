import logging
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