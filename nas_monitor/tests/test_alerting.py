import pytest
from datetime import datetime, timedelta

from nas_monitor.shemas import Metrics
from nas_monitor.models import Device
from nas_monitor.config import config
from nas_monitor.alerting.checkers.cpu import CpuTempChecker, CpuLoadChecker
from nas_monitor.alerting.checkers.ram import RamUsageChecker
from nas_monitor.alerting.checkers.zfs import ZfsUsageChecker
from nas_monitor.alerting.checkers.storage import StorageSmartChecker

@pytest.fixture
def clean_throttle_cache():
    from nas_monitor.alerting.base import _THROTTLE_CACHE
    _THROTTLE_CACHE.clear()
    yield
    _THROTTLE_CACHE.clear()

@pytest.fixture
def device():
    dev = Device(name="test_device", type="unknown", enabled=True)
    dev.id = 1
    return dev

@pytest.mark.asyncio
async def test_cpu_temp_checker(device, clean_throttle_cache, mocker):
    mock_alert = mocker.patch('nas_monitor.alerting.base.BaseChecker.alert', new_callable=mocker.AsyncMock)
    checker = CpuTempChecker()
    
    # Normal temp
    metric_ok = Metrics(device_name="cpu", label="temp", value=40.0)
    assert not await checker.check(metric_ok, device)
    mock_alert.assert_not_called()
    
    # High temp
    metric_high = Metrics(device_name="cpu", label="temp", value=config.ALERT_CPU_TEMP_THRESHOLD + 5)
    assert await checker.check(metric_high, device)
    mock_alert.assert_called_once()

@pytest.mark.asyncio
async def test_ram_usage_checker(device, clean_throttle_cache, mocker):
    mock_alert = mocker.patch('nas_monitor.alerting.base.BaseChecker.alert', new_callable=mocker.AsyncMock)
    checker = RamUsageChecker()
    
    # Normal usage
    metric_ok = Metrics(device_name="ram", label="usage_percent", value=50.0)
    assert not await checker.check(metric_ok, device)
    
    # High usage
    metric_high = Metrics(device_name="ram", label="usage_percent", value=config.ALERT_RAM_USAGE_THRESHOLD + 1)
    assert await checker.check(metric_high, device)
    mock_alert.assert_called_once()

@pytest.mark.asyncio
async def test_zfs_usage_checker(device, clean_throttle_cache, mocker):
    mock_alert = mocker.patch('nas_monitor.alerting.base.BaseChecker.alert', new_callable=mocker.AsyncMock)
    checker = ZfsUsageChecker()
    
    # Normal
    metric_ok = Metrics(device_name="pool1", label="usage_percent", value=80.0)
    assert not await checker.check(metric_ok, device)
    
    # High
    metric_high = Metrics(device_name="pool1", label="usage_percent", value=config.ALERT_ZFS_USAGE_THRESHOLD + 1)
    assert await checker.check(metric_high, device)
    mock_alert.assert_called_once()

@pytest.mark.asyncio
async def test_storage_smart_checker(device, clean_throttle_cache, mocker):
    mock_alert = mocker.patch('nas_monitor.alerting.base.BaseChecker.alert', new_callable=mocker.AsyncMock)
    checker = StorageSmartChecker()
    
    # OK (1.0)
    metric_ok = Metrics(device_name="sda", label="health", value=1.0)
    assert not await checker.check(metric_ok, device)
    
    # FAIL (0.0)
    metric_fail = Metrics(device_name="sda", label="health", value=0.0)
    assert await checker.check(metric_fail, device)
    mock_alert.assert_called_once()

@pytest.mark.asyncio
async def test_throttling(device, clean_throttle_cache, mocker):
    mock_info = mocker.patch('logging.info')
    mock_debug = mocker.patch('logging.debug')
    
    checker = CpuTempChecker()
    metric_high = Metrics(device_name="cpu", label="temp", value=99.0)
    
    # First call - should alert
    await checker.check(metric_high, device)
    mock_info.assert_called() # Alert logged
    
    mock_info.reset_mock()
    
    # Second call immediately - should throttle
    await checker.check(metric_high, device)
    mock_info.assert_not_called() # No alert logged
    mock_debug.assert_called() # Throttle logged

@pytest.mark.asyncio
async def test_cpu_load_checker(device, clean_throttle_cache, mocker):
    mock_alert = mocker.patch('nas_monitor.alerting.base.BaseChecker.alert', new_callable=mocker.AsyncMock)
    checker = CpuLoadChecker()
    
    # High load value
    metric_high_load = Metrics(device_name="cpu", label="load", value=config.ALERT_CPU_LOAD_THRESHOLD + 5)

    # 1. Short duration (should not alert)
    mock_get_duration = mocker.patch.object(checker, 'get_duration_since_value_change', new_callable=mocker.AsyncMock)
    mock_get_duration.return_value = timedelta(minutes=config.ALERT_CPU_LOAD_DURATION_MINUTES - 1)
    
    assert not await checker.check(metric_high_load, device)
    mock_alert.assert_not_called()
    
    # 2. Long duration (should alert)
    mock_get_duration.return_value = timedelta(minutes=config.ALERT_CPU_LOAD_DURATION_MINUTES + 1)
    
    assert await checker.check(metric_high_load, device)
    mock_alert.assert_called_once()
