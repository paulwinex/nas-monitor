import asyncio
import json
import shutil
from abc import ABC, abstractmethod
from datetime import datetime

import psutil

from nas_monitor.shemas import Metrics

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

    async def collect(self) -> list[Metrics]:
        metrics = []
        # CPU load
        load = psutil.cpu_percent(interval=None)
        metrics.append(Metrics(device_name="cpu", label="load", value=load))
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
            metrics.append(Metrics(device_name="cpu", label="temp", value=cpu_temp))
        return metrics


class RAMCollector(BaseCollector):
    dev_type = 'ram'

    async def collect(self) -> list[Metrics]:
        mem = psutil.virtual_memory()
        return [
            Metrics(device_name="ram", label="usage_percent", value=mem.percent),
            Metrics(device_name="ram", label="used_gb", value=round(mem.used / (1024 ** 3), 2))
        ]


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
        if not smartctl_is_available:
            return []
        metrics = []
        # get device list
        proc = await asyncio.create_subprocess_exec(
            "smartctl", "--scan", "--json",
            stdout=asyncio.subprocess.PIPE
        )
        stdout, _ = await proc.communicate()
        devices = json.loads(stdout).get("devices", [])
        for dev in devices:
            path = dev['name']
            p = await asyncio.create_subprocess_exec(
                "smartctl", "-a", path, "--json",
                stdout=asyncio.subprocess.PIPE
            )
            out, _ = await p.communicate()
            data = json.loads(out)
            sn = data.get("serial_number", path).strip()
            # temperature
            temp = data.get("temperature", {}).get("current", 0)
            metrics.append(Metrics(device_name=sn, label="temp", value=float(temp)))
            is_passed = data.get("smart_status", {}).get("passed", True)
            # collect errors (SATA/NVMe)
            reallocated = 0
            pending = 0
            # for SATA
            for attr in data.get("ata_smart_attributes", {}).get("table", []):
                name = attr.get("name")
                raw_val = attr.get("raw", {}).get("value", 0)
                if name == "Reallocated_Sector_Ct":
                    reallocated = raw_val
                elif name == "Current_Pending_Sector":
                    pending = raw_val
            # for NVMe
            nvme_err = data.get("nvme_smart_health_information_log", {}).get("media_errors", 0)
            total_errors = reallocated + pending + nvme_err
            # compute status
            if not is_passed:
                health_status = 2  # Critical: hard drive is broken :(
            elif total_errors > 50:
                health_status = 2  # Critical: to many bad sectors!!!
            elif total_errors > 5:
                health_status = 1  # Warning: first errors found!
            else:
                health_status = 0  # OK: no errors
            metrics.append(Metrics(device_name=sn, label='health', value=health_status))
        return metrics


class ZFSCollector(BaseCollector):
    dev_type = "zfs_pool"

    async def collect(self) -> list[Metrics]:
        if not zfs_is_available:
            return []
        metrics = []
        cmd = ["zpool", "list", "-H", "-p", "-o", "name,size,alloc"]
        proc = await asyncio.create_subprocess_exec(*cmd, stdout=asyncio.subprocess.PIPE)
        stdout, _ = await proc.communicate()
        for line in stdout.decode().strip().split('\n'):
            if not line: continue
            name, size, alloc = line.split()
            usage = (int(alloc) / int(size) * 100) if int(size) > 0 else 0
            metrics.append(Metrics(device_name=name, label="usage_percent", value=round(usage, 2)))
        return metrics
