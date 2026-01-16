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
                
                # Cleanup the path/name to find potential serials
                dev_name = vdev_path.split('/')[-1]
                
                # Try to extract the core identifier
                clean_name = dev_name.replace('-part', '').replace('_1', '')
                for segment in clean_name.split('_'):
                    if len(segment) > 8: # probable SN or WWN
                        mapping[segment] = current_pool
                
                # Handle /dev/nvme0n1p3 format specifically
                # Use regex to strip the partition part (pX)
                base_nvme = re.sub(r'p\d+$', '', dev_name)
                mapping[base_nvme] = current_pool

                
                # Always map the verbatim name found in zpool status
                mapping[dev_name] = current_pool
                mapping[vdev_path] = current_pool

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
        # Use 'zfs list' for USABLE capacity instead of 'zpool list' which is RAW capacity
        proc = await asyncio.create_subprocess_exec(
            "zfs", "list", "-H", "-p", "-o", "name,avail,used", 
            stdout=asyncio.subprocess.PIPE
        )
        stdout, _ = await proc.communicate()
        if stdout:
            for line in stdout.decode().strip().split('\n'):
                if '/' in line: continue # skip datasets, only root pools
                name, avail, used = line.split()
                # Use raw bytes for more accurate summing before rounding
                avail_bytes = int(avail)
                used_bytes = int(used)
                total_bytes = avail_bytes + used_bytes
                
                # Convert to human readable like '26.0T' or '500G'
                tb = total_bytes / (1024**4)
                if tb >= 1:
                    size_str = f"{tb:.1f}T"
                else:
                    gb = total_bytes / (1024**3)
                    size_str = f"{gb:.1f}G"
                    
                await Device.update_or_create(
                    name=name,
                    defaults={"type": "zfs_pool", "details": {"max_size": size_str}}
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
                        # Improved partial match for serials (often prefix/suffix matches)
                        for zfs_sn, p_name in sn_to_pool.items():
                            if sn in zfs_sn or zfs_sn in sn:
                                pool_name = p_name
                                break
                    
                    # One more check: sometimes /dev/ name is used in zpool status
                    if pool_name is None:
                        # we would need more info from zpool status here but for now 
                        # let's trust _get_zfs_serial_mapping's detection of vdev paths
                        pass

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