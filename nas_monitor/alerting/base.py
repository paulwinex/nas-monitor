import logging
import os
from abc import ABC, abstractmethod
from datetime import datetime, timedelta, timezone
from typing import List

from jinja2 import Environment, FileSystemLoader

from nas_monitor.models import Device, RawMetric
from nas_monitor.shemas import Metrics

# Throttle cache: {(device_name, check_class_name): last_alert_timestamp}
_THROTTLE_CACHE = {}

class BaseChecker(ABC):
    device_type: str = None
    metrics_label: str = None
    message_template: str = None

    def __init__(self):
        template_dir = os.path.join(os.path.dirname(__file__), 'templates')
        self.jinja_env = Environment(loader=FileSystemLoader(template_dir))

    @abstractmethod
    async def check(self, data: Metrics, device: Device) -> bool:
        """
        Check metric value and trigger alert if condition is met.
        Must be implemented by subclasses.
        Returns True if alert was triggered.
        """
        pass

    async def alert(self, data: Metrics, device: Device, context: dict = None, throttle_minutes: int = 60) -> bool:
        """
        Send alert if not throttled.
        Returns True if alert condition was processed (even if throttled).
        """
        cache_key = (device.name, self.__class__.__name__)
        now = datetime.now(timezone.utc)
        
        last_alert = _THROTTLE_CACHE.get(cache_key)
        if last_alert:
             if now - last_alert < timedelta(minutes=throttle_minutes):
                 logging.debug(f"Alert throttled for {cache_key}")
                 return True

        _THROTTLE_CACHE[cache_key] = now

        context = context or {}
        context.update({
            "device": device,
            "metric": data,
            "timestamp": now
        })

        try:
            template = self.jinja_env.get_template(self.message_template)
            message = template.render(**context)
            logging.info(f"ALERT [{self.__class__.__name__}]: {message}")
            
            # Placeholder for actual notification sending (e.g. Telegram)

            return True
            
        except Exception as e:
            logging.error(f"Failed to render/send alert: {e}")
            return False

    async def get_history(self, device_id: int, label: str, duration: timedelta) -> List[RawMetric]:
        """
        Get recent metrics history from DB.
        """
        since = datetime.now(timezone.utc) - duration
        return await RawMetric.filter(
            device_id=device_id, 
            label=label, 
            timestamp__gte=since
        ).order_by("timestamp").all()

    async def get_duration_since_value_change(self, device_id: int, label: str, threshold_value: float, operator: str = ">") -> timedelta:
        """
        Calculate how long the value has been satisfying the condition.
        Simple implementation: checks last history entries.
        """
        history = await self.get_history(device_id, label, timedelta(hours=24))
        
        if not history:
            return timedelta(0)

        duration = timedelta(0)
        # Iterate backwards
        for i in range(len(history) - 1, -1, -1):
            val = history[i].value
            match = False
            if operator == ">" and val > threshold_value: match = True
            elif operator == ">=" and val >= threshold_value: match = True
            elif operator == "<" and val < threshold_value: match = True
            elif operator == "<=" and val <= threshold_value: match = True
            elif operator == "==" and val == threshold_value: match = True
            
            if match:
                if i > 0:
                     duration += (history[i].timestamp - history[i-1].timestamp)
            else:
                break
        
        return duration
