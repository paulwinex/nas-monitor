import asyncio
import json
import logging
import platform
import re
import shutil

import psutil

from nas_monitor.models import Device

zfs_is_available = bool(shutil.which('zfs'))


async def _get_zfs_serial_mapping() -> dict[str, str]:
    if not zfs_is_available:
        return {}
    mapping = {}
    try:
        proc = await asyncio.create_subprocess_exec(
            "zpool", "status",
            stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE
        )
        stdout, _ = await proc.communicate()
        if not stdout:
            return mapping

        current_pool = None
        content = stdout.decode()

        for line in content.split('\n'):
            line = line.strip()
            if line.startswith("pool:"):
                current_pool = line.split(":")[1].strip()
            if any(status in line for status in ["ONLINE", "DEGRADED", "FAULTED"]):
                parts = line.split()
                if not parts: continue
                vdev_path = parts[0]
                # skip special devices (raidz, mirror)
                if vdev_path == current_pool or any(x in vdev_path for x in ["raidz", "mirror", "logs", "cache"]):
                    continue
                try:
                    sn_candidate = vdev_path.split('_')[-1].split('-part')[0]
                    mapping[sn_candidate] = current_pool
                except IndexError:
                    continue
    except Exception as e:
        print(f"Error mapping ZFS devices: {e}")
    return mapping


async def get_cpu_model_name() -> str:
    try:
        proc = await asyncio.create_subprocess_exec(
            "lscpu", stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE
        )
        stdout, _ = await proc.communicate()
        if stdout:
            for line in stdout.decode().split('\n'):
                if "Model name" in line:
                    return line.split(':', 1)[1].strip()
    except (OSError, ValueError):
        pass
    return platform.processor()


async def get_ram_info():
    total_gb = round(psutil.virtual_memory().total / (1024 ** 3), 2)
    ram_details = {"total_gb": total_gb, "type": "Unknown", "speed_mhz": "Unknown"}
    try:
        proc = await asyncio.create_subprocess_exec(
            "dmidecode", "-t", "memory", stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE
        )
        stdout, _ = await proc.communicate()
        if stdout:
            output = stdout.decode()
            speed_match = re.search(r"Speed: (\d+) MT/s", output)
            type_match = re.search(r"Type: (DDR\d+)", output)
            if speed_match: ram_details["speed_mhz"] = speed_match.group(1)
            if type_match: ram_details["type"] = type_match.group(1)
    except OSError:
        pass

    return ram_details


async def perform_inventory():
    logging.info("Starting deep system inventory scan...")

    cpu_freq = psutil.cpu_freq()
    cpu_details = {
        "model": await get_cpu_model_name(),
        "architecture": platform.machine(),
        "cores_physical": psutil.cpu_count(logical=False),
        "cores_logical": psutil.cpu_count(logical=True),
        "freq_min_mhz": round(cpu_freq.min, 1) if cpu_freq else 0,
        "freq_max_mhz": round(cpu_freq.max, 1) if cpu_freq else 0,
    }
    await Device.update_or_create(
        name="cpu",
        defaults={
            "type": "cpu",
            "details": cpu_details
        }
    )

    ram_info = await get_ram_info()
    await Device.update_or_create(
        name="ram",
        defaults={
            "type": "ram",
            "details": ram_info
        }
    )

    await Device.update_or_create(
        name="net",
        defaults={
            "type": "network",
            "poll_interval": 2,
            "details": {
                "description": "Aggregated traffic from all physical and bridge interfaces",
                "monitored_interfaces": [
                    name for name in psutil.net_if_stats().keys()
                    if name != 'lo' and not name.startswith(('veth', 'fw'))
                ]
            }
        }
    )

    sn_to_pool = await _get_zfs_serial_mapping()
    try:
        proc = await asyncio.create_subprocess_exec("zpool", "list", "-H", "-o", "name,size", stdout=asyncio.subprocess.PIPE)
        stdout, _ = await proc.communicate()
        if stdout:
            for line in stdout.decode().strip().split('\n'):
                name, size = line.split()
                await Device.update_or_create(
                    name=name,
                    defaults={"type": "zfs_pool", "details": {"max_size": size}}
                )
    except OSError:
        pass

    try:
        proc = await asyncio.create_subprocess_exec("smartctl", "--scan", "--json", stdout=asyncio.subprocess.PIPE)
        stdout, _ = await proc.communicate()
        if stdout:
            scan_data = json.loads(stdout)
            for dev_info in scan_data.get("devices", []):
                path = dev_info['name']
                p_info = await asyncio.create_subprocess_exec("smartctl", "-i", path, "--json", stdout=asyncio.subprocess.PIPE)
                out_info, _ = await p_info.communicate()
                data = json.loads(out_info)

                sn = data.get("serial_number", "").strip()
                model = data.get("model_name", "Unknown")
                rotation_rate = data.get("rotation_rate", 0)
                drive_type = "ssd" if rotation_rate == 0 else "hdd"

                if sn:
                    pool_name = sn_to_pool.get(sn)
                    if pool_name is None:
                        for zfs_sn, p_name in sn_to_pool.items():
                            if sn in zfs_sn or zfs_sn in sn:
                                pool_name = p_name
                                break

                    await Device.update_or_create(
                        name=sn,
                        defaults={
                            "type": "storage",
                            "details": {
                                "model": model,
                                "path": path,
                                "zfs_pool": pool_name,
                                "drive_type": drive_type,
                                "rotation_rate": rotation_rate
                            }
                        }
                    )
    except Exception as e:
        logging.error(f"Disk inventory error: {e}")

    logging.info("Inventory scan complete.")