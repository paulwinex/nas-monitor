import asyncio
import json
import logging
import os
from functools import cache 
import shutil
from typing import Dict, List, Optional, Any


async def run_cmd(args: List[str]) -> str:
    """Run a system command asynchronously and return stdout."""
    try:
        proc = await asyncio.create_subprocess_exec(
            *args,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )
        stdout, stderr = await proc.communicate()
        if proc.returncode != 0:
            # Some tools might return non-zero but still have useful output (like smartctl)
            # We'll just return stdout for now and let the parser handle it
            pass
        return stdout.decode().strip()
    except Exception as e:
        # logging.debug(f"Error running {' '.join(args)}: {e}")
        return ""

@cache
def is_tool_available(name: str) -> bool:
    """Check if a command-line tool is available."""
    return shutil.which(name) is not None


async def get_physical_disks() -> List[Dict[str, Any]]:
    """Get list of physical disks and their basic info using lsblk."""
    if not is_tool_available("lsblk"):
        return []

    # Get all block devices to build a mapping from partition/kname to serial
    cmd = ["lsblk", "-J", "-b", "-o", "NAME,TYPE,ROTA,TRAN,SIZE,MOUNTPOINT,SERIAL,MODEL,KNAME,PKNAME"]
    output = await run_cmd(cmd)
    if not output:
        return []

    try:
        data = json.loads(output)
        devices = []
        kname_to_serial = {} # Map for all knames (including children) to parent serial

        def process_dev(dev, parent_serial=None):
            sn = (dev.get("serial") or "").strip()
            if not sn and parent_serial:
                sn = parent_serial
            
            kname = dev.get("kname") or dev.get("name")
            if kname:
                kname_to_serial[kname] = sn
            
            for child in dev.get("children", []):
                process_dev(child, sn)

        for dev in data.get("blockdevices", []):
            process_dev(dev)
            if dev.get("type") == "disk":
                # Determine type: SSD, HDD, NVMe
                tran = (dev.get("tran") or "").lower()
                # rota can be boolean true/false or string "1"/"0" depending on lsblk version
                rota_val = dev.get("rota")
                rota = rota_val is True or str(rota_val) == "1"
                
                disk_type = "HDD"
                if "nvme" in tran or "nvme" in (dev.get("name") or ""):
                    disk_type = "NVMe"
                elif not rota:
                    disk_type = "SSD"
                
                # Collect partitions
                partitions = []
                for child in dev.get("children", []):
                    if child.get("type") == "part":
                        partitions.append({
                            "name": child.get("name"),
                            "kname": f"/dev/{child.get('kname')}",
                            "mountpoint": child.get("mountpoint"),
                            "size": int(child.get("size") or 0)
                        })

                devices.append({
                    "name": dev.get("name"),
                    "kname": f"/dev/{dev.get('kname') or dev.get('name')}",
                    "model": (dev.get("model") or "").strip(),
                    "serial": (dev.get("serial") or "").strip(),
                    "size": int(dev.get("size") or 0),
                    "type": disk_type,
                    "partitions": partitions,
                    "mountpoint": dev.get("mountpoint"),
                    "kname_short": dev.get("kname") or dev.get("name")
                })
        
        # Attach the mapping to the result for later use
        return devices, kname_to_serial
    except (json.JSONDecodeError, ValueError):
        return [], {}


async def get_disk_usage(path: str) -> Dict[str, float]:
    """Get disk usage (total, used, free) in GB for a mount point."""
    try:
        if not path or not os.path.exists(path):
            return {}
        
        stat = os.statvfs(path)
        total = (stat.f_blocks * stat.f_frsize)
        free = (stat.f_bfree * stat.f_frsize)
        used = total - free
        
        return {
            "total_gb": round(total / (1024**3), 2),
            "used_gb": round(used / (1024**3), 2),
            "free_gb": round(free / (1024**3), 2),
            "percent": round((used / total * 100), 1) if total > 0 else 0
        }
    except Exception:
        return {}


async def get_smart_info(device_path: str) -> Dict[str, Any]:
    """Get SMART data for a device using smartctl."""
    if not is_tool_available("smartctl"):
        return {}

    cmd = ["smartctl", "-a", "-j", device_path]
    output = await run_cmd(cmd)
    if not output:
        return {}

    try:
        data = json.loads(output)
        
        # Temperature search
        temp = data.get("temperature", {}).get("current")
        
        if temp is None:
            # Check NVMe log
            temp = data.get("nvme_smart_health_information_log", {}).get("temperature")
        
        if temp is None:
            # Check ATA attributes
            for attr in data.get("ata_smart_attributes", {}).get("table", []):
                if attr.get("name") in ["Temperature_Celsius", "Airflow_Temperature_Cel"]:
                    temp = attr.get("raw", {}).get("value")
                    break

        if temp is None:
            temp = 0
        
        # Power on hours
        hours = data.get("power_on_time", {}).get("hours", 0)
        
        # Errors (reallocated sectors, pending, etc.)
        reallocated = 0
        pending = 0
        # SATA/ATA
        for attr in data.get("ata_smart_attributes", {}).get("table", []):
            name = attr.get("name")
            raw_val = attr.get("raw", {}).get("value", 0)
            if name == "Reallocated_Sector_Ct":
                reallocated = raw_val
            elif name == "Current_Pending_Sector":
                pending = raw_val
        
        # NVMe errors
        nvme_err = data.get("nvme_smart_health_information_log", {}).get("media_errors", 0)
        
        total_errors = reallocated + pending + nvme_err
        is_passed = data.get("smart_status", {}).get("passed", True)

        # Compute health status
        if not is_passed:
            health_status = 3  # Critical: hard drive is broken :(
        elif total_errors > 50:
            health_status = 2  # Critical: to many bad sectors!!!
        elif total_errors > 5:
            health_status = 1  # Warning: first errors found!
        else:
            health_status = 0  # OK: no errors
        
        return {
            "temperature": temp,
            "power_on_hours": hours,
            "errors": total_errors,
            "smart_passed": is_passed,
            "health_status": health_status
        }
    except (json.JSONDecodeError, ValueError):
        return {}

async def get_zfs_pools() -> List[Dict[str, Any]]:
    """Get list of ZFS pools and their status."""
    if not is_tool_available("zpool"):
        return []

    # zpool list -H -o name,health,size,alloc,free
    cmd = ["zpool", "list", "-H", "-p", "-o", "name,health,size,alloc,free"]
    output = await run_cmd(cmd)
    if not output:
        return []

    pools = []
    for line in output.strip().split('\n'):
        if not line: continue
        parts = line.split()
        if len(parts) >= 5:
            name, health, size, alloc, free = parts
            pools.append({
                "name": name,
                "status": health, # ONLINE, DEGRADED, etc.
                "total_bytes": int(size),
                "used_bytes": int(alloc),
                "free_bytes": int(free),
                "total_gb": round(int(size) / (1024**3), 2),
                "used_gb": round(int(alloc) / (1024**3), 2)
            })
    return pools


async def get_zfs_pool_disks(pool_name: str, kname_to_serial: Dict[str, str]) -> List[str]:
    """Get serial numbers of disks in a ZFS pool."""
    if not is_tool_available("zpool"):
        return []

    # zpool status -L <pool> shows actual device names if possible
    cmd = ["zpool", "status", "-L", pool_name]
    output = await run_cmd(cmd)
    if not output:
        return []

    # Extract device names (e.g., sda, nvme0n1, sda1, nvme0n1p3)
    import re
    # Match various forms: sda, sda1, nvme0n1, nvme0n1p3
    dev_names = re.findall(r'\b(sd[a-z]+[0-9]*|nvme[0-9]+n[0-9]+(?:p[0-9]+)?)\b', output)
    
    unique_names = list(set(dev_names))
    serials = []
    
    for dev in unique_names:
        # Use the mapping we built from lsblk
        sn = kname_to_serial.get(dev)
        if sn:
            serials.append(sn)
            
    return sorted(list(set(serials)))


async def get_zfs_pool_real_usage(pool_name: str) -> Dict[str, Any]:
    """Get real space usage of a ZFS pool (usable space, not raw pool size)."""
    if not is_tool_available("zfs"):
        return {}

    # zfs list -H -p -o name,used,avail,refer
    # Only for the root dataset of the pool
    cmd = ["zfs", "list", "-H", "-p", "-o", "name,used,avail", pool_name]
    output = await run_cmd(cmd)
    if not output:
        return {}

    parts = output.strip().split()
    if len(parts) >= 3:
        name, used, avail = parts
        used_b = int(used)
        avail_b = int(avail)
        total_b = used_b + avail_b
        return {
            "used_bytes": used_b,
            "avail_bytes": avail_b,
            "total_bytes": total_b,
            "used_gb": round(used_b / (1024**3), 2),
            "total_gb": round(total_b / (1024**3), 2),
            "percent": round((used_b / total_b * 100), 1) if total_b > 0 else 0
        }
    return {}

async def collect_all_disk_info():
    """Main collector function that aggregates all data."""
    disks, kname_to_serial = await get_physical_disks()
    
    # ZFS Info first to map disks to pools
    pools = await get_zfs_pools()
    zfs_serials = {} # serial -> pool_name
    pool_usage_map = {} # pool_name -> real_usage
    for pool in pools:
        pool['real_usage'] = await get_zfs_pool_real_usage(pool['name'])
        pool['disks'] = await get_zfs_pool_disks(pool['name'], kname_to_serial)
        pool_usage_map[pool['name']] = pool['real_usage']
        for sn in pool['disks']:
            if sn:
                zfs_serials[sn] = pool['name']

    # Enrich disks with SMART and usage
    for disk in disks:
        # SMART
        disk['smart'] = await get_smart_info(disk['kname'])
        
        # Check if part of ZFS
        pool_name = zfs_serials.get(disk['serial'])
        disk['zfs_pool'] = pool_name
        
        # Usage (sum of all mounted partitions)
        disk['usage'] = {
            "total_gb": 0,
            "used_gb": 0,
            "free_gb": 0,
            "percent": 0
        }
        
        mounted_partitions = 0
        total_used_b = 0
        total_size_b = 0
        
        # Check root disk mount
        if disk.get('mountpoint'):
            usage = await get_disk_usage(disk['mountpoint'])
            if usage:
                total_used_b += usage['used_gb'] * (1024**3)
                total_size_b += usage['total_gb'] * (1024**3)
                mounted_partitions += 1
                
        # Check partitions
        for part in disk.get('partitions', []):
            if part.get('mountpoint'):
                usage = await get_disk_usage(part['mountpoint'])
                if usage:
                    total_used_b += usage['used_gb'] * (1024**3)
                    total_size_b += usage['total_gb'] * (1024**3)
                    mounted_partitions += 1
        
        if mounted_partitions > 0:
            disk['usage'] = {
                "total_gb": round(total_size_b / (1024**3), 2),
                "used_gb": round(total_used_b / (1024**3), 2),
                "free_gb": round((total_size_b - total_used_b) / (1024**3), 2),
                "percent": round((total_used_b / total_size_b * 100), 1) if total_size_b > 0 else 0
            }
        elif pool_name and pool_name in pool_usage_map:
            # Fallback to ZFS pool usage if no system mountpoints found
            z_usage = pool_usage_map[pool_name]
            if z_usage:
                disk['usage'] = {
                    "total_gb": z_usage.get('total_gb', 0),
                    "used_gb": z_usage.get('used_gb', 0),
                    "free_gb": round(z_usage.get('avail_bytes', 0) / (1024**3), 2),
                    "percent": z_usage.get('percent', 0)
                }
            else:
                disk['usage'] = None
        else:
            disk['usage'] = None

    return {
        "disks": disks, 
        "zfs_pools": pools
    }

async def main():
    print("--- Disk & ZFS Information Collector ---")
    data = await collect_all_disk_info()
    
    print("\n[ Physical Disks ]")
    for d in data['disks']:
        status = []
        if d['usage']: status.append("Mounted")
        if d['zfs_pool']: status.append(f"ZFS Pool: {d['zfs_pool']}")
        if not status: status.append("Unmounted/Available")
        
        print(f"Disk: {d['kname']} ({d['type']}, {d['model']}) [{', '.join(status)}]")
        print(f"  Serial: {d['serial']}")
        print(f"  Size: {round(d['size']/(1024**3), 2)} GB")
        if d['smart']:
            print(f"  SMART: Temp={d['smart']['temperature']}C, Errors={d['smart']['errors']}, Status={'OK' if d['smart']['smart_passed'] else 'FAIL'}")
        if d['usage']:
            print(f"  System Usage: {d['usage']['used_gb']}/{d['usage']['total_gb']} GB ({d['usage']['percent']}%)")
        print("-" * 20)

    print("\n[ ZFS Pools ]")
    if not data['zfs_pools']:
        print("No ZFS pools found or ZFS tools not installed.")
    for p in data['zfs_pools']:
        print(f"Pool: {p['name']} ({p['status']})")
        u = p['real_usage']
        if u:
            print(f"  Real Usage: {u['used_gb']}/{u['total_gb']} GB ({u['percent']}%)")
        print(f"  Member Disks: {', '.join(p['disks']) if p['disks'] else 'Unknown'}")
        print("-" * 20)

if __name__ == "__main__":
    asyncio.run(main())
