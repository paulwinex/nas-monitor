from nas_monitor.alerting.base import BaseChecker
from nas_monitor.shemas import Metrics
from nas_monitor.models import Device
from nas_monitor.config import config

class StorageTempChecker(BaseChecker):
    device_type = 'storage'
    metrics_label = 'temp'
    message_template = 'storage_temp.md'

    async def check(self, data: Metrics, device: Device) -> bool:
        if data.value > config.ALERT_STORAGE_TEMP_THRESHOLD:
            await self.alert(
                data=data, 
                device=device,
                context={'threshold': config.ALERT_STORAGE_TEMP_THRESHOLD},
                throttle_minutes=config.ALERT_THROTTLE_MINUTES
            )
            return True
        return False

class StorageSmartChecker(BaseChecker):
    device_type = 'storage'
    metrics_label = 'health'
    message_template = 'storage_smart.md'

    async def check(self, data: Metrics, device: Device) -> bool:
        # 0  - unknown/fail
        # 1  - PASSED
        # 1< - errors
        if data.value != 1.0:
             await self.alert(
                data=data, 
                device=device,
                context={'status': 'FAIL' if data.value == 0 else 'UNKNOWN'},
                throttle_minutes=config.ALERT_THROTTLE_MINUTES
            )
             return True
        return False
