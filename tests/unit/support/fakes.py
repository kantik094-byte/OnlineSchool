from app.application.exceptions import InvalidTokenError, AuthenticationError
from app.application.interfaces.repositories import UserRepository, LectureRepository, SectionRepository, ModuleRepository, CourseRepository
from app.application.interfaces.services.identity_provider import IdentityProvider
from app.application.interfaces.services.password_hasher import PasswordHasher
from app.application.interfaces.services.token_service import TokenService
from app.application.interfaces.unit_of_work import UnitOfWork
from app.domain.entities import Course
from app.domain.entities.lecture import Lecture
from app.domain.entities.module import Module
from app.domain.entities.section import Section
from app.domain.entities.user import User


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

    async def get_for_update(self, course_id) -> Course | None:
        return self.items.get(course_id)

    async def list(self):
        return list(self.items.values())

    async def add(self, course) -> None:
        self.items[course.id] = course

    async def update(self, course) -> None:
        self.items[course.id] = course

    async def remove(self, course) -> None:
        self.items.pop(course.id, None)




class FakeModuleRepository(ModuleRepository):
    def __init__(self) -> None:
        self.items = {}

    async def get_by_id(self, module_id):
        return self.items.get(module_id)

    async def get_by_ids(self, module_ids):
        return [self.items[module_id] for module_id in module_ids if module_id in self.items]

    async def get_for_update(self, module_id) -> Module | None:
        return self.items.get(module_id)

    async def add(self, module) -> None:
        self.items[module.id] = module

    async def update(self, module) -> None:
        self.items[module.id] = module

    async def update_many(self, modules: list[Module]) -> None:
        for module in modules:
            self.items[module.id] = module

    async def remove(self, module) -> None:
        self.items.pop(module.id, None)





class FakeSectionRepository(SectionRepository):
    def __init__(self) -> None:
        self.items = {}

    async def get_by_id(self, section_id):
        return self.items.get(section_id)

    async def get_by_ids(self, section_ids):
        return [self.items[section_id] for section_id in section_ids if section_id in self.items]

    async def get_for_update(self, section_id) -> Section | None:
        return self.items.get(section_id)

    async def add(self, section) -> None:
        self.items[section.id] = section

    async def update(self, section) -> None:
        self.items[section.id] = section

    async def update_many(self, sections: list[Section]) -> None:
        for section in sections:
            self.items[section.id] = section

    async def remove(self, section) -> None:
        self.items.pop(section.id, None)




class FakeLectureRepository(LectureRepository):
    def __init__(self) -> None:
        self.items = {}

    async def get_by_id(self, lecture_id):
        return self.items.get(lecture_id)

    async def get_by_ids(self, lecture_ids):
        return [self.items[lecture_id] for lecture_id in lecture_ids if lecture_id in self.items]

    async def get_for_update(self, lecture_id) -> Lecture | None:
        return self.items.get(lecture_id)

    async def add(self, lecture) -> None:
        self.items[lecture.id] = lecture

    async def update(self, lecture) -> None:
        self.items[lecture.id] = lecture

    async def update_many(self, lectures: list[Lecture]) -> None:
        for lecture in lectures:
            self.items[lecture.id] = lecture

    async def remove(self, lecture) -> None:
        self.items.pop(lecture.id, None)




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

    # async def __aenter__(self):
    #     return self
    #
    # async def __aexit__(self, exc_type, exc, tb):
    #     return None

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