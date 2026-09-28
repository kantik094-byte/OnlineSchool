from uuid import uuid4

import pytest

from app.application.exceptions import InvalidTokenError, AuthenticationError
from app.application.interfaces.repositories import UserRepository, LectureRepository, SectionRepository, ModuleRepository, CourseRepository
from app.application.interfaces.services.identity_provider import IdentityProvider
from app.application.interfaces.services.password_hasher import PasswordHasher
from app.application.interfaces.services.token_service import TokenService
from app.application.interfaces.unit_of_work import UnitOfWork
from app.domain.entities.user import User, UserRole


class FakeIdentityProvider(IdentityProvider):
    def __init__(self, user: User | None = None) -> None:
        self._user = user

    async def get_current_user(self) -> User:
        if self._user is None:
            raise AuthenticationError('Bearer token was not provided.')
        return self._user



class FakeCourseRepository(CourseRepository):
    def __init__(self) -> None:
        self.items = {}

    async def get_by_id(self, course_id):
        return self.items.get(course_id)

    async def list(self):
        return list(self.items.values())

    async def add(self, course) -> None:
        self.items[course.id] = course

    async def update(self, course) -> None:
        self.items[course.id] = course




class FakeModuleRepository(ModuleRepository):
    def __init__(self) -> None:
        self.items = {}

    async def get_by_id(self, module_id):
        return self.items.get(module_id)

    async def get_by_ids(self, module_ids):
        return [self.items[module_id] for module_id in module_ids if module_id in self.items]

    async def add(self, module) -> None:
        self.items[module.id] = module

    async def update(self, module) -> None:
        self.items[module.id] = module




class FakeSectionRepository(SectionRepository):
    def __init__(self) -> None:
        self.items = {}

    async def get_by_id(self, section_id):
        return self.items.get(section_id)

    async def get_by_ids(self, section_ids):
        return [self.items[section_id] for section_id in section_ids if section_id in self.items]

    async def add(self, section) -> None:
        self.items[section.id] = section

    async def update(self, section) -> None:
        self.items[section.id] = section




class FakeLectureRepository(LectureRepository):
    def __init__(self) -> None:
        self.items = {}

    async def get_by_id(self, lecture_id):
        return self.items.get(lecture_id)

    async def get_by_ids(self, lecture_ids):
        return [self.items[lecture_id] for lecture_id in lecture_ids if lecture_id in self.items]

    async def add(self, lecture) -> None:
        self.items[lecture.id] = lecture

    async def update(self, lecture) -> None:
        self.items[lecture.id] = lecture




class FakeUserRepository(UserRepository):
    def __init__(self) -> None:
        self.items: dict[str, User] = {}

    async def get_by_id(self, user_id):
        for user in self.items.values():
            if user.id == user_id:
                return user
        return None

    async def get_by_email(self, email: str):
        return self.items.get(email)

    async def add(self, user: User) -> None:
        self.items[user.email] = user



class FakeUnitOfWork(UnitOfWork):
    def __init__(self) -> None:
        self.courses = FakeCourseRepository()
        self.modules = FakeModuleRepository()
        self.sections = FakeSectionRepository()
        self.lectures = FakeLectureRepository()
        self.users = FakeUserRepository()
        self.committed = False

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc, tb):
        return None

    async def commit(self) -> None:
        self.committed = True

    async def rollback(self) -> None:
        return None



class StubPasswordHasher(PasswordHasher):
    def hash(self, raw_password: str) -> str:
        return f'hashed::{raw_password}'

    def verify(self, raw_password: str, hashed_password: str) -> bool:
        return hashed_password == f'hashed::{raw_password}'



class StubTokenService(TokenService):
    def __init__(self) -> None:
        self._users = {}

    def create_access_token(self, user_id, role: str) -> str:
        token = f'token-for-{user_id}-{role}'
        self._users[token] = user_id
        return token

    def get_user_id(self, token: str):
        if token in self._users:
            return self._users[token]
        raise InvalidTokenError('Token is invalid.')


@pytest.fixture
def admin() -> User:
    return User(id=uuid4(), email='admin@example.com', hashed_password='hashed::x', role=UserRole.ADMIN)


@pytest.fixture
def student() -> User:
    return User(id=uuid4(), email='student@example.com', hashed_password='hashed::x', role=UserRole.STUDENT)
