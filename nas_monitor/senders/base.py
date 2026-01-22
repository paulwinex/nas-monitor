from abc import ABC, abstractmethod

class BaseSender(ABC):
    sender_name: str = None

    @abstractmethod
    async def send_message(self, message: str) -> None:
        """
        Send message
        """
        pass
