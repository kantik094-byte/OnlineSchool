from uuid import uuid4

import pytest

from app.application.exceptions import UserAlreadyExistsError, InvalidCredentialsError
from app.application.use_cases.auth.login_user import LoginUserUseCase, LoginUserCommand
from app.application.use_cases.auth.register_user import RegisterUserUseCase, RegisterUserCommand
from app.domain.entities.user import UserRole, User
from tests.conftest import FakeUnitOfWork


@pytest.mark.asyncio
async def test_register_user_creates_student_and_commits(uow, password_hasher) -> None:
    use_case = RegisterUserUseCase(uow=uow, password_hasher=password_hasher)

    result = await use_case.execute(
        RegisterUserCommand(
            email='student@example.com',
            password='secret123',
        )
    )

    assert result.email == 'student@example.com'
    assert result.role is UserRole.STUDENT
    assert result.hashed_password == 'hashed::secret123'
    assert uow.committed is True


@pytest.mark.asyncio
async def test_register_user_raises_error_when_email_already_exists(password_hasher) -> None:
    uow = FakeUnitOfWork()
    existing_user = User(
        id=uuid4(),
        email='student@example.com',
        hashed_password='hashed::secret123',
        role=UserRole.STUDENT,
    )
    await uow.users.add(existing_user)

    use_case = RegisterUserUseCase(uow=uow, password_hasher=password_hasher)

    with pytest.raises(UserAlreadyExistsError):
        await use_case.execute(
            RegisterUserCommand(
                email='student@example.com',
                password='another-password',
            )
        )


@pytest.mark.asyncio
async def test_login_user_returns_access_token(password_hasher, uow, token_service) -> None:
    user = User(
        id=uuid4(),
        email='admin@example.com',
        hashed_password='hashed::secret123',
        role=UserRole.ADMIN,
    )
    await uow.users.add(user)

    use_case = LoginUserUseCase(
        uow=uow,
        password_hasher=password_hasher,
        token_service=token_service,
    )

    result = await use_case.execute(
        LoginUserCommand(
            email='admin@example.com',
            password='secret123',
        )
    )

    assert result.token_type == 'bearer'
    assert result.access_token.startswith('token-for-')


@pytest.mark.asyncio
async def test_login_user_raises_error_when_email_is_unknown(password_hasher, token_service) -> None:
    use_case = LoginUserUseCase(
        uow=FakeUnitOfWork(),
        password_hasher=password_hasher,
        token_service=token_service,
    )

    with pytest.raises(InvalidCredentialsError):
        await use_case.execute(
            LoginUserCommand(
                email='missing@example.com',
                password='secret123',
            )
        )


@pytest.mark.asyncio
async def test_login_user_raises_error_when_password_is_invalid(password_hasher, token_service, uow) -> None:
    user = User(
        id=uuid4(),
        email='admin@example.com',
        hashed_password='hashed::secret123',
        role=UserRole.ADMIN,
    )
    await uow.users.add(user)

    use_case = LoginUserUseCase(
        uow=uow,
        password_hasher=password_hasher,
        token_service=token_service,
    )

    with pytest.raises(InvalidCredentialsError):
        await use_case.execute(
            LoginUserCommand(
                email='admin@example.com',
                password='wrong-password',
            )
        )