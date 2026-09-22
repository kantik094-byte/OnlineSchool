from app.application.exceptions import AccessDeniedError
from app.application.interfaces.services.identity_provider import IdentityProvider
from app.domain.entities.user import User


async def require_content_manager(idp: IdentityProvider) -> User:
    user = await idp.get_current_user()
    if not user.can_manage_content():
        raise AccessDeniedError('Admin access is required.')
    return user
