import pytest

from tests.fakes import FakeUserRepository, FakeUnitOfWork, StubPasswordHasher, StubTokenService, FakeCourseRepository, \
    FakeModuleRepository, FakeSectionRepository, FakeLectureRepository, FakeIdentityProvider


@pytest.fixture
async def fake_user_repo() -> FakeUserRepository:
    return FakeUserRepository()


@pytest.fixture
async def uow() -> FakeUnitOfWork:
    return FakeUnitOfWork()


@pytest.fixture
def password_hasher() -> StubPasswordHasher:
    return StubPasswordHasher()


@pytest.fixture
def token_service() -> StubTokenService:
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

