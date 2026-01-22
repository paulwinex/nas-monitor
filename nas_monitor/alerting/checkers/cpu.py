from nas_monitor.alerting.base import BaseChecker
from nas_monitor.config import config
from nas_monitor.models import Device
from nas_monitor.shemas import Metrics


class CpuTempChecker(BaseChecker):
    device_type = 'cpu'
    metrics_label = 'temp'
    message_template = 'cpu_temp.md'

    async def check(self, data: Metrics, device: Device) -> bool:
        if data.value > config.ALERT_CPU_TEMP_THRESHOLD:
            await self.alert(
                data=data, 
                device=device,
                context={'threshold': config.ALERT_CPU_TEMP_THRESHOLD},
                throttle_minutes=config.ALERT_THROTTLE_MINUTES
            )
            return True
        return False


class CpuLoadChecker(BaseChecker):
    device_type = 'cpu'
    metrics_label = 'load'
    message_template = 'cpu_load.md'

    async def check(self, data: Metrics, device: Device) -> bool:
        if data.value > config.ALERT_CPU_LOAD_THRESHOLD:
            duration = await self.get_duration_since_value_change(
                device.id, 'load', config.ALERT_CPU_LOAD_THRESHOLD, ">"
            )
            
            duration_minutes = duration.total_seconds() / 60
            
            if duration_minutes > config.ALERT_CPU_LOAD_DURATION_MINUTES:
                 await self.alert(
                    data=data, 
                    device=device,
                    context={'threshold': config.ALERT_CPU_LOAD_THRESHOLD},
                    throttle_minutes=config.ALERT_THROTTLE_MINUTES
                )
                 return True
        return False
