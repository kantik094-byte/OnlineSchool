from fastapi import Request, Security
from fastapi.security import HTTPBearer

from app.application.exceptions import AuthenticationError, InvalidTokenError
from app.application.interfaces.repositories import UserRepository
from app.application.interfaces.services.identity_provider import IdentityProvider
from app.application.interfaces.services.token_service import TokenService
from app.domain.entities.user import User
from app.presentation.api.schemas import ErrorResponse

# auto_error=False: сам HTTPBearer ничего не бросает, ошибку
# в едином формате ErrorResponse отдаст наш IdentityProvider.
bearer_scheme = HTTPBearer(
    auto_error=False,
    description='JWT-токен в заголовке Authorization: Bearer <token>',
)

# Только для OpenAPI: замок в Swagger + описание 401.
# Проверку делает не FastAPI, а use case через IdentityProvider.
AUTH_REQUIRED = [Security(bearer_scheme)]
AUTH_RESPONSES = {
    401: {'description': 'Authentication credentials are missing or invalid.', 'model': ErrorResponse},
}
ADMIN_RESPONSES = {
    **AUTH_RESPONSES,
    403: {'description': 'Admin access is required.', 'model': ErrorResponse},
}


class BearerIdentityProvider(IdentityProvider):
    """HTTP-адаптер: достаёт Bearer-токен из запроса и находит по нему пользователя."""

    def __init__(self, request: Request, token_service: TokenService, users: UserRepository) -> None:
        self._request = request
        self._token_service = token_service
        self._users = users
        self._user: User | None = None

    async def get_current_user(self) -> User:
        if self._user is not None:
            return self._user

        # Тот же парсер, что рисует схему в OpenAPI: одна точка правды.
        credentials = await bearer_scheme(self._request)
        if credentials is None:
            raise AuthenticationError('Bearer token was not provided.')

        try:
            user_id = self._token_service.get_user_id(credentials.credentials)
        except InvalidTokenError as exc:
            raise AuthenticationError(str(exc)) from exc

        user = await self._users.get_by_id(user_id)
        if user is None:
            raise AuthenticationError('User from token was not found.')

        self._user = user
        return user
