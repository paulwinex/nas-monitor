import logging

from nas_monitor.collectors import BaseCollector
from nas_monitor.config import config
from nas_monitor.metrics import add_metrics_batch, get_enabled_devices_by_type

# map collectors by device type
COLLECTORS = {cls.dev_type: cls() for cls in BaseCollector.__subclasses__()}


async def job_collector_task(dev_type: str):
    """Call scheduled task dor device type"""
    devices = await get_enabled_devices_by_type(dev_type)
    if not devices:
        logging.warning('No devices to scan for type: %s', dev_type)
        return
    collector = COLLECTORS.get(dev_type)
    if collector:
        data = await collector.collect()
        enabled_names = {d.name for d in devices}
        filtered_data = [m for m in data if m.device_name in enabled_names]

        if filtered_data:
            await add_metrics_batch(filtered_data)
        else:
            logging.warning('Nothing to write for type: %s', dev_type)
    else:
        logging.warning('No collector for type: %s', dev_type)


def setup_polling(scheduler):
    """Setup polling jobs with intervals from config"""
    # Network
    scheduler.add_job(
        job_collector_task, 'interval', 
        seconds=config.COLLECTOR_INTERVAL_NETWORK, 
        args=['network']
    )
    # CPU
    scheduler.add_job(
        job_collector_task, 'interval', 
        seconds=config.COLLECTOR_INTERVAL_CPU, 
        args=['cpu']
    )
    # RAM
    scheduler.add_job(
        job_collector_task, 'interval', 
        seconds=config.COLLECTOR_INTERVAL_RAM, 
        args=['ram']
    )
    # Hard drives and SSD
    scheduler.add_job(
        job_collector_task, 'interval', 
        seconds=config.COLLECTOR_INTERVAL_STORAGE, 
        args=['storage']
    )
    # ZFS Pool
    scheduler.add_job(
        job_collector_task, 'interval', 
        seconds=config.COLLECTOR_INTERVAL_ZFS_POOL, 
        args=['zfs_pool']
    )
