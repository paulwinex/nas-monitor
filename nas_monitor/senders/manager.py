import importlib
import logging
import pkgutil
from typing import Dict

from nas_monitor.config import config
from nas_monitor.senders.base import BaseSender


class SenderManager:
    def __init__(self):
        self.senders: Dict[str, BaseSender] = {}
        self._initialize_senders()

    def _initialize_senders(self):
        """
        Initialize senders.
        """
        active_providers = config.ALERT_PROVIDERS
        logging.info(f"Initializing alert providers: {active_providers}")

        # Import all provider modules dynamically
        package_name = "nas_monitor.senders.providers"
        package = importlib.import_module(package_name)

        for _, module_name, _ in pkgutil.iter_modules(package.__path__):
            try:
                importlib.import_module(f"{package_name}.{module_name}")
            except ImportError as e:
                logging.error(f"Failed to import provider module {module_name}: {e}")

        # Discover and initialize all BaseSender subclasses
        for cls in BaseSender.__subclasses__():
            sender_name = cls.sender_name
            if sender_name in active_providers:
                try:
                    self.senders[sender_name] = cls()
                    logging.info(f"Sender '{sender_name}' initialized.")
                except Exception as e:
                    logging.error(f"Failed to initialize sender '{sender_name}': {e}")
            else:
                logging.debug(f"Sender '{sender_name}' found but not active in config.")

    async def send_all(self, message: str):
        """
        Send message to all registered senders.
        """
        for name, sender in self.senders.items():
            try:
                await sender.send_message(message)
            except Exception as e:
                logging.error(f"Error sending message via {name}: {e}")

# Global instance
sender_manager = SenderManager()
