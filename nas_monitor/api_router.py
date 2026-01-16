from fastapi import APIRouter, Query, HTTPException
from datetime import datetime, timedelta, timezone
from typing import Optional

from nas_monitor.frontend_config import frontend_config
from nas_monitor.models import Device
from nas_monitor.metrics import (
    fetch_metrics_data,
    get_latest_metrics_by_device,
    get_inventory_grouped
)
from nas_monitor.utils.system_info import (
    get_detailed_system_info,
    host_reboot,
    host_poweroff
)

router = APIRouter(prefix="/api", tags=["api"])


@router.get("/inventory")
async def get_inventory():
    """
    Get full device inventory with grouping by ZFS pools.
    
    Returns:
    - zpools: List of ZFS pools with >1 disk
    - system_devices: CPU, RAM, Network, and standalone storage devices
    """
    try:
        inventory = await get_inventory_grouped()
        return {
            "status": "success",
            "data": inventory
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get inventory: {str(e)}")


@router.get("/config")
async def get_frontend_config():
    """
    Get frontend configuration (update intervals, SMART status levels, etc.)
    """
    config_data = frontend_config.model_dump()
    # Convert keys to lowercase for JavaScript compatibility
    return {
        "status": "success",
        "data": {
            "update_intervals": config_data["UPDATE_INTERVALS"],
            "smart_status_levels": config_data["SMART_STATUS_LEVELS"],
            "chart_history_points": config_data["CHART_HISTORY_POINTS"],
            "raw_metrics_hours": config_data["RAW_METRICS_HOURS"]
        }
    }


@router.get("/metrics")
async def get_metrics(
    history_type: str = Query(..., description="Record types: raw, daily or history"),
    device_types: Optional[list[str]] = Query(None, description="Device types to filter"),
    device_names: Optional[list[str]] = Query(None, description="Specific device names to filter"),
    hours: Optional[int] = Query(None, description="Get metrics for last N hours (for raw metrics)"),
    from_date: Optional[datetime] = None,
    to_date: Optional[datetime] = None
):
    """
    Get metrics with time range filtering.
    
    Parameters:
    - history_type: raw, daily, or history
    - device_types: Optional list of device types to filter
    - hours: Get metrics for last N hours (overrides from_date if provided)
    - from_date: Start time for metrics
    - to_date: End time for metrics
    """
    if history_type not in ["raw", "hourly", "history"]:
        raise HTTPException(status_code=400, detail="history_type must be raw, hourly or history")
    
    # If hours is provided, calculate from_date
    if hours is not None:
        to_date = datetime.now(timezone.utc)
        from_date = to_date - timedelta(hours=hours)
    
    try:
        data = await fetch_metrics_data(
            history_type=history_type,
            device_types=device_types,
            device_names=device_names,
            start_time=from_date,
            end_time=to_date
        )
        return {
            "status": "success",
            "count": len(data),
            "data": data
        }
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch metrics: {str(e)}")


@router.get("/devices")
async def list_devices():
    """
    Get all registered devices (for settings/management)
    """
    try:
        devices = await Device.all().order_by("type", "name")
        return {
            "status": "success",
            "data": [
                {
                    "name": d.name,
                    "type": d.type,
                    "enabled": d.enabled,
                    "details": d.details
                } for d in devices
            ]
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to list devices: {str(e)}")


@router.patch("/devices/{name}")
async def update_device(name: str, payload: dict):
    """
    Update device settings (e.g., enabled status)
    """
    try:
        device = await Device.filter(name=name).first()
        if not device:
            raise HTTPException(status_code=404, detail="Device not found")
        
        if "enabled" in payload:
            device.enabled = bool(payload["enabled"])
            await device.save()
            
        return {
            "status": "success",
            "data": {
                "name": device.name,
                "enabled": device.enabled
            }
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to update device: {str(e)}")


@router.get("/system/info")
async def get_system_info():
    """
    Get detailed host system information.
    """
    try:
        info = await get_detailed_system_info()
        return {
            "status": "success",
            "data": info
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get system info: {str(e)}")


@router.post("/host/restart")
async def restart_host():
    """
    Triggers a system reboot.
    """
    try:
        await host_reboot()
        return {"status": "success", "message": "Reboot triggered"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to reboot: {str(e)}")


@router.post("/host/poweroff")
async def poweroff_host():
    """
    Triggers a system shutdown.
    """
    try:
        await host_poweroff()
        return {"status": "success", "message": "Poweroff triggered"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to poweroff: {str(e)}")


@router.get("/latest")
async def get_latest_metrics(
    device_types: Optional[list[str]] = Query(None, description="Device types to filter")
):
    """
    Get latest metric values for current indicators (temperature, SMART status, etc.)
    
    Returns dict: {device_name: {label: value}}
    """
    try:
        latest = await get_latest_metrics_by_device(device_types=device_types)
        return {
            "status": "success",
            "data": latest
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get latest metrics: {str(e)}")
