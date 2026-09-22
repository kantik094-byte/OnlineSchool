from app.application.interfaces.services.identity_provider import IdentityProvider
from app.domain.entities.user import User


class GetCurrentUserUseCase:
    def __init__(self, idp: IdentityProvider) -> None:
        self.idp = idp

    async def execute(self) -> User:
        return await self.idp.get_current_user()
