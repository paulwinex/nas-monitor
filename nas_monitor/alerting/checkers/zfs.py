from nas_monitor.alerting.base import BaseChecker
from nas_monitor.shemas import Metrics
from nas_monitor.models import Device
from nas_monitor.config import config

class ZfsUsageChecker(BaseChecker):
    device_type = 'zfs_pool'
    metrics_label = 'usage_percent'
    message_template = 'zfs_usage.md'

    async def check(self, data: Metrics, device: Device) -> bool:
        if data.value > config.ALERT_ZFS_USAGE_THRESHOLD:
            await self.alert(
                data=data, 
                device=device,
                context={'threshold': config.ALERT_ZFS_USAGE_THRESHOLD},
                throttle_minutes=config.ALERT_STORAGE_CAPACITY_THRESHOLD
            )
            return True
        return False
