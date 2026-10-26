from abc import ABC, abstractmethod

from app.domain.entities.user import User


class IdentityProvider(ABC):
    """
    Проверка прав пользователя
    """

    @abstractmethod
    async def get_current_user(self) -> User:
        raise NotImplementedError
