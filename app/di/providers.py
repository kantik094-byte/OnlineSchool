from typing import AsyncIterator

from dishka import Provider, Scope, provide, provide_all
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.application.interfaces.repositories import (
    CourseRepository,
    LectureRepository,
    ModuleRepository,
    SectionRepository,
    UserRepository,
)
from app.application.interfaces.services.identity_provider import IdentityProvider
from app.application.interfaces.services.password_hasher import PasswordHasher
from app.application.interfaces.services.token_service import TokenService
from app.application.interfaces.unit_of_work import UnitOfWork
from app.application.use_cases.auth.get_current_user import GetCurrentUserUseCase
from app.application.use_cases.auth.login_user import LoginUserUseCase
from app.application.use_cases.auth.register_user import RegisterUserUseCase
from app.application.use_cases.courses.create_course import CreateCourseUseCase
from app.application.use_cases.courses.get_course import GetCourseUseCase
from app.application.use_cases.courses.get_course_structure import GetCourseStructureUseCase
from app.application.use_cases.courses.get_courses import GetCoursesUseCase
from app.application.use_cases.courses.update_course import UpdateCourseUseCase
from app.application.use_cases.lectures.create_lecture import CreateLectureUseCase
from app.application.use_cases.lectures.get_lecture import GetLectureUseCase
from app.application.use_cases.lectures.update_lecture import UpdateLectureUseCase
from app.application.use_cases.modules.create_module import CreateModuleUseCase
from app.application.use_cases.modules.update_module import UpdateModuleUseCase
from app.application.use_cases.sections.create_sections import CreateSectionUseCase
from app.application.use_cases.sections.update_section import UpdateSectionUseCase
from app.infrastructure.config import get_settings
from app.infrastructure.config.settings import DatabaseSettings, JwtSettings, Settings
from app.infrastructure.database import SqlAlchemyUnitOfWork
from app.infrastructure.security.jwt_token_service import JwtTokenService
from app.infrastructure.security.password_hasher import PwdlibPasswordHasher
from app.presentation.api.security import BearerIdentityProvider


class AuthProvider(Provider):
    # Request нужен BearerIdentityProvider; его в контейнер кладёт
    # FastapiProvider из dishka.integrations.fastapi (подключается в main.py).
    identity_provider = provide(
        BearerIdentityProvider,
        provides=IdentityProvider,
        scope=Scope.REQUEST,
    )


class ConfigProvider(Provider):
    scope = Scope.APP

    @provide
    def settings(self) -> Settings:
        return get_settings()

    @provide
    def database_settings(self, settings: Settings) -> DatabaseSettings:
        return settings.database

    @provide
    def jwt_settings(self, settings: Settings) -> JwtSettings:
        return settings.jwt


class DatabaseProvider(Provider):
    @provide(scope=Scope.APP)
    async def session_factory(self, settings: DatabaseSettings) -> AsyncIterator[async_sessionmaker[AsyncSession]]:
        engine = create_async_engine(settings.url, echo=settings.echo)
        try:
            yield async_sessionmaker(bind=engine, expire_on_commit=False)
        finally:
            await engine.dispose()

    @provide(scope=Scope.REQUEST)
    async def uow(self, session_factory: async_sessionmaker[AsyncSession]) -> AsyncIterator[UnitOfWork]:
        async with SqlAlchemyUnitOfWork(session_factory=session_factory) as uow:
            yield uow

    # Репозитории отдаём отдельно, чтобы read-only use case'ы
    # зависели только от того, что им реально нужно.
    @provide(scope=Scope.REQUEST)
    def courses(self, uow: UnitOfWork) -> CourseRepository:
        return uow.courses

    @provide(scope=Scope.REQUEST)
    def modules(self, uow: UnitOfWork) -> ModuleRepository:
        return uow.modules

    @provide(scope=Scope.REQUEST)
    def sections(self, uow: UnitOfWork) -> SectionRepository:
        return uow.sections

    @provide(scope=Scope.REQUEST)
    def lectures(self, uow: UnitOfWork) -> LectureRepository:
        return uow.lectures

    @provide(scope=Scope.REQUEST)
    def users(self, uow: UnitOfWork) -> UserRepository:
        return uow.users


class SecurityProvider(Provider):
    # Сервисы без состояния: один экземпляр на всё приложение.
    scope = Scope.APP

    password_hasher = provide(PwdlibPasswordHasher, provides=PasswordHasher)
    token_service = provide(JwtTokenService, provides=TokenService)


class UseCasesProvider(Provider):
    # Dishka сам читает аннотации __init__ и собирает зависимости,
    # поэтому ручные фабрики «return XUseCase(uow=uow)» не нужны.
    scope = Scope.REQUEST

    use_cases = provide_all(
        GetCoursesUseCase,
        GetCourseUseCase,
        GetCourseStructureUseCase,
        GetLectureUseCase,
        CreateCourseUseCase,
        UpdateCourseUseCase,
        CreateModuleUseCase,
        UpdateModuleUseCase,
        CreateSectionUseCase,
        UpdateSectionUseCase,
        CreateLectureUseCase,
        UpdateLectureUseCase,
        RegisterUserUseCase,
        LoginUserUseCase,
        GetCurrentUserUseCase,
    )
