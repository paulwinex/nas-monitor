from nas_monitor.alerting.base import BaseChecker
from nas_monitor.shemas import Metrics
from nas_monitor.models import Device
from nas_monitor.config import config

class RamUsageChecker(BaseChecker):
    device_type = 'ram'
    metrics_label = 'usage_percent'
    message_template = 'ram_usage.md'

    async def check(self, data: Metrics, device: Device) -> bool:
        if data.value > config.ALERT_RAM_USAGE_THRESHOLD:
            await self.alert(
                data=data, 
                device=device,
                context={'threshold': config.ALERT_RAM_USAGE_THRESHOLD},
                throttle_minutes=config.ALERT_THROTTLE_MINUTES
            )
            return True
        return False

class RamTempChecker(BaseChecker):
    device_type = 'ram'
    metrics_label = 'temp'
    message_template = 'ram_temp.md'

    async def check(self, data: Metrics, device: Device) -> bool:
        if data.value > config.ALERT_RAM_TEMP_THRESHOLD:
            await self.alert(
                data=data, 
                device=device,
                context={'threshold': config.ALERT_RAM_TEMP_THRESHOLD},
                throttle_minutes=config.ALERT_THROTTLE_MINUTES
            )
            return True
        return False
