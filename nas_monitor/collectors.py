import asyncio
import json
import os
import shutil
from abc import ABC, abstractmethod
from datetime import datetime

import psutil

from nas_monitor.shemas import Metrics
from nas_monitor.utils.disk_utils import collect_all_disk_info

zfs_is_available = bool(shutil.which('zfs'))
smartctl_is_available = bool(shutil.which('smartctl'))
psutil.cpu_percent()    # temp call to init monitor


class BaseCollector(ABC):
    dev_type: str = None

    @abstractmethod
    async def collect(self) -> list[Metrics]:
        ...


class CPUCollector(BaseCollector):
    dev_type = 'cpu'

    def __init__(self, alpha=0.3):
        self.alpha = alpha
        self.smoothed_load = None

    async def collect(self) -> list[Metrics]:
        metrics = []
        # CPU load
        load = psutil.cpu_percent(interval=None)
        
        # Exponential Moving Average smoothing
        if self.smoothed_load is None:
            self.smoothed_load = load
        else:
            self.smoothed_load = self.alpha * load + (1 - self.alpha) * self.smoothed_load
            
        metrics.append(Metrics(device_name="cpu", label="load", value=round(self.smoothed_load, 1)))
        
        # CPU temperature
        temps = psutil.sensors_temperatures()
        cpu_temp = None
        # find the sensor
        for name in ['coretemp', 'k10temp', 'cpu_thermal', 'soc_thermal']:
            if name in temps:
                for entry in temps[name]:
                    if entry.label.startswith('Package') or entry.label == '':
                        cpu_temp = entry.current
                        break
                if not cpu_temp and temps[name]:
                    cpu_temp = temps[name][0].current
                break
        if cpu_temp is not None:
            metrics.append(Metrics(device_name="cpu", label="temp", value=round(cpu_temp, 1)))
        return metrics



class RAMCollector(BaseCollector):
    dev_type = 'ram'

    async def collect(self) -> list[Metrics]:
        mem = psutil.virtual_memory()
        metrics = [
            Metrics(device_name="ram", label="usage_percent", value=mem.percent),
            Metrics(device_name="ram", label="used_gb", value=round(mem.used / (1024 ** 3), 2))
        ]

        # RAM temperature (try to find matching sensors)
        try:
            temps = psutil.sensors_temperatures()
            mem_temps = []
            for name, entries in temps.items():
                name_lower = name.lower()
                # jc42 is a common RAM temp sensor driver
                if any(x in name_lower for x in ['dimm', 'mem', 'acpitz', 'pch_', 'jc42', 'gigabyte']):
                    for entry in entries:
                        if entry.current > 0:
                            mem_temps.append(entry.current)
            
            if mem_temps:
                # Use max or average? Usually people care about the hottest stick
                avg_temp = sum(mem_temps) / len(mem_temps)
                metrics.append(Metrics(device_name="ram", label="temp", value=round(avg_temp, 1)))
        except Exception:
            pass

        return metrics


class NetCollector(BaseCollector):
    dev_type = "network"

    def __init__(self):
        self.prev_io = psutil.net_io_counters(pernic=False)
        self.prev_time = datetime.now()

    async def collect(self) -> list[Metrics]:
        now = datetime.now()
        curr_io = psutil.net_io_counters(pernic=False)
        dt = (now - self.prev_time).total_seconds()
        metrics = []
        if dt > 0:
            up_speed = (curr_io.bytes_sent - self.prev_io.bytes_sent) / dt / 1024
            down_speed = (curr_io.bytes_recv - self.prev_io.bytes_recv) / dt / 1024
            metrics.extend([
                Metrics(device_name="net", label="upload", value=round(up_speed, 2)),
                Metrics(device_name="net", label="download", value=round(down_speed, 2))
            ])
        self.prev_io = curr_io
        self.prev_time = now
        return metrics


class StorageCollector(BaseCollector):
    dev_type = 'storage'

    async def collect(self) -> list[Metrics]:
        data = await collect_all_disk_info()
        metrics = []
        
        for disk in data.get('disks', []):
            sn = disk.get('serial') or disk.get('name')
            
            # SMART data
            smart = disk.get('smart', {})
            if smart:
                metrics.append(Metrics(device_name=sn, label="temp", value=float(smart.get('temperature', 0))))
                metrics.append(Metrics(device_name=sn, label="health", value=float(smart.get('health_status', 0))))
            
            # Disk Usage (if mounted in system)
            usage = disk.get('usage')
            if usage:
                metrics.extend([
                    Metrics(device_name=sn, label="used_gb", value=usage['used_gb']),
                    Metrics(device_name=sn, label="total_gb", value=usage['total_gb']),
                    Metrics(device_name=sn, label="usage_percent", value=usage['percent'])
                ])
                
        return metrics



class ZFSCollector(BaseCollector):
    dev_type = "zfs_pool"

    async def collect(self) -> list[Metrics]:
        data = await collect_all_disk_info()
        metrics = []
        
        for pool in data.get('zfs_pools', []):
            name = pool['name']
            usage = pool.get('real_usage', {})
            if usage:
                metrics.append(Metrics(device_name=name, label="usage_percent", value=usage['percent']))
                metrics.append(Metrics(device_name=name, label="used_gb", value=usage['used_gb']))
                metrics.append(Metrics(device_name=name, label="total_gb", value=usage['total_gb']))
                
        return metrics




