from abc import ABC, abstractmethod

from app.domain.entities.user import User


class IdentityProvider(ABC):
    """
    «Кто сейчас выполняет действие?».

    Application-слой не знает ни про HTTP, ни про JWT, ни про заголовки:
    он просто спрашивает текущего пользователя. Откуда тот берётся
    (Bearer-токен, cookie, CLI-аргумент, тестовая заглушка) решает адаптер.
    """

    @abstractmethod
    async def get_current_user(self) -> User:
        """Raises AuthenticationError, если пользователя определить нельзя."""
        raise NotImplementedError
