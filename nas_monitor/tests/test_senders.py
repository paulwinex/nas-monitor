import pytest
from unittest.mock import AsyncMock, patch, MagicMock
from nas_monitor.senders.manager import SenderManager
# Use the new path for TelegramSender
from nas_monitor.senders.providers.telegram import TelegramSender


@pytest.mark.asyncio
async def test_telegram_sender_success():
    # Setup mock
    with patch("aiohttp.ClientSession.post") as mock_post:
        # Configure the mock to return a context manager
        mock_response = AsyncMock()
        mock_response.status = 200
        mock_post.return_value.__aenter__.return_value = mock_response

        # Test Sender
        sender = TelegramSender()
        sender.token = "test_token"
        sender.chat_id = "test_chat_id"
        sender.api_url = "http://test-api.com"

        await sender.send_message("Test Message")

        # Assertions
        mock_post.assert_called_once()
        args, kwargs = mock_post.call_args
        assert kwargs["json"]["chat_id"] == "test_chat_id"
        assert kwargs["json"]["text"] == "Test Message"


@pytest.mark.asyncio
async def test_manager_dynamic_loading():
    # Mock pkgutil and importlib to simulate provider discovery
    with patch("pkgutil.iter_modules") as mock_iter_modules, \
            patch("importlib.import_module") as mock_import_module:
        # Setup mock for module iteration
        mock_iter_modules.return_value = []  # No actual files to find, we'll rely on subclass detection

        # Configure mock_import_module to return a mock object with __path__ attribute
        mock_package = MagicMock()
        mock_package.__path__ = ["/fake/path"]
        mock_import_module.return_value = mock_package

        # We need to manually register the TelegramSender as subclass of BaseSender
        # which it already is by import.
        # But we want to test if Manager picks it up.

        # Initialize Manager
        # We need to ensure config has 'telegram' enabled
        with patch("nas_monitor.config.config.ALERT_PROVIDERS", ["telegram"]):
            manager = SenderManager()

            # Since we imported TelegramSender at top, it is a subclass of BaseSender
            # The manager should have found it and initialized it because it's in ALERT_PROVIDERS
            assert "telegram" in manager.senders
            assert isinstance(manager.senders["telegram"], TelegramSender)


@pytest.mark.asyncio
async def test_manager_send_all():
    # Mock senders
    mock_telegram = AsyncMock(spec=TelegramSender)

    # Initialize Manager with mocked senders
    manager = SenderManager()
    manager.senders = {"telegram": mock_telegram}

    # Run send_all
    await manager.send_all("Manager Test Message")

    # Assertions
    mock_telegram.send_message.assert_called_once_with("Manager Test Message")
