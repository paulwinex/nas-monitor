import asyncio
import json
import os
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
        
        # Get mount points to match disks with partitions
        # Resolve all devices to their real paths to handle LVM/dm-crypt/etc.
        partitions = {}
        for p in psutil.disk_partitions(all=True):
            try:
                # Resolve symlinks like /dev/mapper/rpool-ROOT... or /dev/nvme0n1p3
                real_dev = os.path.realpath(p.device)
                partitions[real_dev] = p.mountpoint
                partitions[p.device] = p.mountpoint
            except Exception:
                continue
        
        # get device list
        proc = await asyncio.create_subprocess_exec(
            "smartctl", "--scan", "--json",
            stdout=asyncio.subprocess.PIPE
        )
        stdout, _ = await proc.communicate()
        devices = json.loads(stdout).get("devices", [])
        for dev in devices:
            path = dev['name']
            real_path = os.path.realpath(path)
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
            
            # Disk Usage for standalone disks
            mount_point = None
            # Check dev, real dev, and potential partitions
            search_paths = [path, real_path]
            for sp in search_paths:
                if sp in partitions:
                    mount_point = partitions[sp]
                    break
            
            if not mount_point:
                # Check partitions like /dev/sda1 or /dev/nvme0n1p1
                for part_dev, mnt in partitions.items():
                    if part_dev.startswith(path) or part_dev.startswith(real_path):
                        mount_point = mnt
                        break
            
            if mount_point:
                try:
                    usage = psutil.disk_usage(mount_point)
                    metrics.extend([
                        Metrics(device_name=sn, label="used_gb", value=round(usage.used / (1024**3), 2)),
                        Metrics(device_name=sn, label="total_gb", value=round(usage.total / (1024**3), 2)),
                        Metrics(device_name=sn, label="usage_percent", value=usage.percent)
                    ])
                except Exception:
                    pass


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
                health_status = 3  # Critical: hard drive is broken :(
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
        # Use 'zfs list' to get usage percent based on USABLE space
        cmd = ["zfs", "list", "-H", "-p", "-o", "name,used,avail"]
        proc = await asyncio.create_subprocess_exec(*cmd, stdout=asyncio.subprocess.PIPE)
        stdout, _ = await proc.communicate()
        for line in stdout.decode().strip().split('\n'):
            if not line or '/' in line: continue
            try:
                parts = line.split()
                if len(parts) < 3: continue
                name, used, avail = parts
                used_bytes = int(used)
                avail_bytes = int(avail)
                total_bytes = used_bytes + avail_bytes
                
                usage_percent = (used_bytes / total_bytes * 100) if total_bytes > 0 else 0
                
                metrics.append(Metrics(device_name=name, label="usage_percent", value=round(usage_percent, 2)))
                metrics.append(Metrics(device_name=name, label="used_gb", value=round(used_bytes / (1024**3), 2)))
                metrics.append(Metrics(device_name=name, label="total_gb", value=round(total_bytes / (1024**3), 2)))
            except (ValueError, IndexError):
                continue
        return metrics

class RAMCollector(BaseCollector):
    dev_type = "ram"

    async def collect(self) -> list[Metrics]:
        mem = psutil.virtual_memory()
        metrics = [
            Metrics(device_name="ram", label="usage_percent", value=mem.percent),
            Metrics(device_name="ram", label="used_gb", value=round(mem.used / (1024**3), 2))
        ]
        
        # RAM temperature (try to find matching sensors)
        try:
            temps = psutil.sensors_temperatures()
            mem_temp = None
            for name, entries in temps.items():
                name_lower = name.lower()
                if any(x in name_lower for x in ['dimm', 'mem', 'acpitz', 'pch_']):
                    for entry in entries:
                        if entry.current > 0:
                            mem_temp = entry.current
                            break
                if mem_temp: break
                
            if mem_temp is not None:
                metrics.append(Metrics(device_name="ram", label="temp", value=round(mem_temp, 1)))
        except Exception:
            pass
            
        return metrics



