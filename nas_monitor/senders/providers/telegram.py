import logging

import aiohttp

from nas_monitor.config import config
from nas_monitor.senders.base import BaseSender


class TelegramSender(BaseSender):
    sender_name = "telegram"

    def __init__(self):
        self.token = config.TELEGRAM_BOT_TOKEN
        self.chat_id = config.TELEGRAM_CHAT_ID
        self.api_url = f"https://api.telegram.org/bot{self.token}/sendMessage"

    async def send_message(self, message: str) -> None:
        if not self.token or not self.chat_id:
            logging.error(f"TelegramSender: Token or Chat ID not configured. Token present: {bool(self.token)}, ChatID present: {bool(self.chat_id)}")
            return

        payload = {
            "chat_id": self.chat_id,
            "text": message,
            "parse_mode": "Markdown"
        }

        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(self.api_url, json=payload) as response:
                    if response.status != 200:
                        error_text = await response.text()
                        logging.error(f"TelegramSender: Failed to send message. Status: {response.status}, Response: {error_text}")
                    else:
                        logging.info("TelegramSender: Message sent successfully.")
        except Exception as e:
            logging.error(f"TelegramSender: Error sending message: {e}")
