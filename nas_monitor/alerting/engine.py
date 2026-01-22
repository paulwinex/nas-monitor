import logging
import asyncio
import importlib
import pkgutil
from typing import List, Dict, Type

from nas_monitor.shemas import Metrics
from nas_monitor.models import Device
from nas_monitor.alerting.base import BaseChecker
import nas_monitor.alerting.checkers

class AlertEngine:
    def __init__(self):
        self.checkers: Dict[tuple, List[BaseChecker]] = {}
        self._checkers_loaded = False

    def _load_checkers(self):
        """
        Dynamically load all checker classes from the checkers package.
        """
        package = nas_monitor.alerting.checkers
        for _, module_name, _ in pkgutil.iter_modules(package.__path__):
            full_module_name = f"{package.__name__}.{module_name}"
            importlib.import_module(full_module_name)

        # Register loaded subclasses
        for cls in BaseChecker.__subclasses__():
            if not cls.device_type:
                continue
            key = (cls.device_type, cls.metrics_label)
            if key not in self.checkers:
                self.checkers[key] = []
            
            self.checkers[key].append(cls())
            logging.info(f"Registered checker {cls.__name__} for {cls.device_type}/{cls.metrics_label}")
        
        self._checkers_loaded = True

    async def process(self, metrics: List[Metrics], devices: List[Device]):
        """
        Entry point for processing metrics.
        """
        if not self._checkers_loaded:
            self._load_checkers()

        tasks = []

        device_map = {d.name: d for d in devices}

        for metric in metrics:
            device = device_map.get(metric.device_name)
            if not device:
                continue
            # Find checkers for this specific metric
            key = (device.type, metric.label)
            checkers = self.checkers.get(key, [])

            for checker in checkers:
                tasks.append(self._safe_check(checker, metric, device))
        
        if tasks:
            await asyncio.gather(*tasks)

    async def _safe_check(self, checker: BaseChecker, metric: Metrics, device: Device):
        # Wrap in try-except to prevent one checker from failing the whole batch
        try:
            await checker.check(metric, device)
        except Exception as e:
            logging.error(f"Error in checker {checker.__class__.__name__}: {e}")


alert_engine = AlertEngine()
