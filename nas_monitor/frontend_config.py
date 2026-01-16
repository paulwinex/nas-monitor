from pydantic_settings import BaseSettings, SettingsConfigDict


class FrontendConfig(BaseSettings):
    """Configuration for frontend (returned via API)"""
    
    model_config = SettingsConfigDict(
        env_prefix="FRONTEND_",
        extra="allow"
    )
    
    # Update intervals for frontend polling (in seconds)
    UPDATE_INTERVALS: dict[str, int] = {
        "cpu": 5,
        "ram": 5,
        "network": 3,
        "storage": 60,
        "zfs_pool": 60
    }
    
    # SMART health status levels
    SMART_STATUS_LEVELS: dict[int, str] = {
        0: "OK",           # No errors
        1: "Warning",      # First errors found (5-50 bad sectors)
        2: "Critical",     # Too many bad sectors (>50)
        3: "Failed"        # SMART test failed, drive is broken
    }
    
    # Chart settings
    CHART_HISTORY_POINTS: int = 40
    RAW_METRICS_HOURS: int = 1  # How many hours of raw metrics to fetch


# Global frontend config instance
frontend_config = FrontendConfig()


