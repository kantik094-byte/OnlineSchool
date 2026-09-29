from uuid import uuid4

import pytest

from app.domain.entities.user import User, UserRole
from tests.fakes import FakeUserRepository, FakeUnitOfWork, StubPasswordHasher, StubTokenService, FakeCourseRepository, \
    FakeModuleRepository, FakeSectionRepository, FakeLectureRepository, FakeIdentityProvider


@pytest.fixture
async def fake_user_repo() -> FakeUserRepository:
    return FakeUserRepository()


@pytest.fixture
async def uow() -> FakeUnitOfWork:
    return FakeUnitOfWork()


@pytest.fixture
def fake_password_hasher() -> StubPasswordHasher:
    return StubPasswordHasher()


@pytest.fixture
def fake_token_service() -> StubTokenService:
    return StubTokenService()


@pytest.fixture
def fake_course_repo() -> FakeCourseRepository:
    return FakeCourseRepository()


@pytest.fixture
def fake_module_repo() -> FakeModuleRepository:
    return FakeModuleRepository()


@pytest.fixture
def fake_section_repo() -> FakeSectionRepository:
    return FakeSectionRepository()


@pytest.fixture
def fake_lecture_repo() -> FakeLectureRepository:
    return FakeLectureRepository()


@pytest.fixture
def admin() -> User:
    return User(id=uuid4(), email='admin@example.com', hashed_password='hashed::x', role=UserRole.ADMIN)


@pytest.fixture
def student() -> User:
    return User(id=uuid4(), email='student@example.com', hashed_password='hashed::x', role=UserRole.STUDENT)
