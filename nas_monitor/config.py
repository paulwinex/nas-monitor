from pydantic_settings import BaseSettings, SettingsConfigDict
from pathlib import Path


DATA_PATH = Path(__file__, '../../data').resolve()
DATA_PATH.mkdir(parents=True, exist_ok=True)


class AppConfig(BaseSettings):
    """Application configuration using pydantic-settings"""
    
    model_config = SettingsConfigDict(
        env_file=".env",
        env_prefix="NAS_",
        extra="allow"
    )
    
    # Database
    DB_PATH: str = f"sqlite://{DATA_PATH}/metrics_db.sqlite3"
    
    # Polling intervals for collectors (in seconds)
    COLLECTOR_INTERVAL_CPU: int = 5
    COLLECTOR_INTERVAL_RAM: int = 5
    COLLECTOR_INTERVAL_NETWORK: int = 3
    COLLECTOR_INTERVAL_STORAGE: int = 60
    COLLECTOR_INTERVAL_ZFS_POOL: int = 60  # 1 minute
    
    # Metrics retention
    RAW_RETENTION_HOURS: int = 3
    DAILY_RETENTION_DAYS: int = 7
    HISTORY_RETENTION_DAYS: int = 365
    
    # Aggregation intervals (in minutes)
    AGGREGATION_INTERVAL_DAILY: int = 5  # raw -> daily every 5 min
    AGGREGATION_INTERVAL_HISTORY: int = 60  # daily -> history every hour
    
    # API settings
    API_HOST: str = "0.0.0.0"
    API_PORT: int = 8000
    CORS_ORIGINS: list[str] = ["*"]
    
    # Alerting settings
    ALERT_THROTTLE_MINUTES: int = 10
    ALERT_CPU_TEMP_THRESHOLD: float = 60.0
    ALERT_CPU_LOAD_THRESHOLD: float = 90.0
    ALERT_CPU_LOAD_DURATION_MINUTES: int = 5
    ALERT_STORAGE_TEMP_THRESHOLD: float = 45.0
    ALERT_STORAGE_CAPACITY_THRESHOLD: float = 60

    ALERT_RAM_USAGE_THRESHOLD: float = 95.0
    ALERT_RAM_TEMP_THRESHOLD: float = 70.0  # approximate warning temp for RAM
    
    ALERT_ZFS_USAGE_THRESHOLD: float = 90.0

    # Disable tasks (for testing)
    DISABLE_TASKS: bool = False


# Global config instance
config = AppConfig()


