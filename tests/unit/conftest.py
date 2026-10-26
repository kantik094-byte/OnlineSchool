import pytest

from tests.unit.support.factories import ContentFactory, UserFactory
from tests.unit.support.fakes import FakeUserRepository, FakeUnitOfWork, StubPasswordHasher, StubTokenService, FakeCourseRepository, \
    FakeModuleRepository, FakeSectionRepository, FakeLectureRepository


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
def content(uow) -> ContentFactory:
    return ContentFactory(uow)


@pytest.fixture
def users() -> UserFactory:
    return UserFactory()
