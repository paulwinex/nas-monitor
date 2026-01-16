import asyncio
import os
import platform
import psutil
import logging

async def run_cmd(args: list[str]) -> str:
    try:
        proc = await asyncio.create_subprocess_exec(
            *args,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )
        stdout, stderr = await proc.communicate()
        return stdout.decode().strip()
    except Exception as e:
        logging.error(f"Error running {' '.join(args)}: {e}")
        return ""

async def get_detailed_system_info() -> dict:
    """Collect detailed system information."""
    info = {
        "os": platform.system(),
        "os_release": platform.release(),
        "os_version": platform.version(),
        "hostname": platform.node(),
        "architecture": platform.machine(),
        "cpu_count": psutil.cpu_count(logical=True),
        "cpu_freq": None,
        "kernel": platform.release(),
    }
    
    # Try to get more detailed OS info on Linux
    if os.path.exists("/etc/os-release"):
        try:
            with open("/etc/os-release", "r") as f:
                for line in f:
                    if line.startswith("PRETTY_NAME="):
                        info["os_pretty"] = line.split("=")[1].strip().strip('"')
                        break
        except Exception:
            pass

    try:
        freq = psutil.cpu_freq()
        if freq:
            info["cpu_freq"] = f"{freq.max:.0f} MHz"
    except Exception:
        pass

    # Boot time
    info["boot_time"] = datetime_from_timestamp(psutil.boot_time()).isoformat()

    return info

def datetime_from_timestamp(ts):
    from datetime import datetime, timezone
    return datetime.fromtimestamp(ts, tz=timezone.utc)

def find_admin_command(name: str) -> str:
    """Find absolute path of an administrative command."""
    for path in ["/usr/sbin", "/sbin", "/usr/bin", "/bin"]:
        full_path = os.path.join(path, name)
        if os.path.isfile(full_path) and os.access(full_path, os.X_OK):
            return full_path
    return name

async def host_reboot():
    """Trigger system reboot."""
    logging.warning("Host reboot triggered!")
    cmd = find_admin_command("reboot")
    await run_cmd([cmd])

async def host_poweroff():
    """Trigger system poweroff."""
    logging.warning("Host poweroff triggered!")
    cmd = find_admin_command("poweroff")
    await run_cmd([cmd])

def get_system_uptime() -> int:
    """Get system uptime in seconds using /proc/uptime if available, else psutil."""
    try:
        if os.path.exists("/proc/uptime"):
            with open("/proc/uptime", "r") as f:
                uptime_seconds = float(f.readline().split()[0])
                return int(uptime_seconds)
    except Exception:
        pass
    
    # Fallback to psutil
    import time
    return int(time.time() - psutil.boot_time())
