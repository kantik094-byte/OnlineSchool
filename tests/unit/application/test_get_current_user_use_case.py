from uuid import uuid4

import pytest

from app.application.use_cases.auth.get_current_user import GetCurrentUserUseCase
from app.domain.entities.user import User, UserRole
from tests.fakes import FakeIdentityProvider

PASSWORD = '123'

@pytest.mark.asyncio
@pytest.mark.parametrize('user_role', [UserRole.ADMIN, UserRole.STUDENT])
async def test_get_current_user(uow, fake_password_hasher, user_role) -> None:
    user = User(id=uuid4(), email='example@mail.ru', hashed_password=fake_password_hasher.hash(PASSWORD), role=user_role)

    use_case = GetCurrentUserUseCase(FakeIdentityProvider(user))

    result = await use_case.execute()

    assert result == user