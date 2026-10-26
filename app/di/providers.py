from typing import AsyncIterator

from dishka import Provider, Scope, provide, provide_all
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

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
from app.application.use_cases import (CreateCourseUseCase, CreateLectureUseCase, CreateModuleUseCase, CreateSectionUseCase,
                                       DeleteCourseUseCase,
                                       DeleteLectureUseCase, DeleteModuleUseCase, DeleteSectionUseCase, GetCourseStructureUseCase,
                                       GetCourseUseCase,
                                       GetCoursesUseCase, GetCurrentUserUseCase, GetLectureUseCase, LoginUserUseCase,
                                       RegisterUserUseCase,
                                       UpdateCourseUseCase, UpdateLectureUseCase, UpdateModuleUseCase, UpdateSectionUseCase)
from app.infrastructure.config import get_settings
from app.infrastructure.config.settings import DatabaseSettings, JwtSettings, Settings
from app.infrastructure.database import SqlAlchemyUnitOfWork
from app.infrastructure.database.engine import build_engine
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
        engine = build_engine(settings.url, echo=settings.echo)
        try:
            yield async_sessionmaker(bind=engine, expire_on_commit=False)
        finally:
            await engine.dispose()

    # Двойной UoW. Сначала открывал провайдер, потом открывал UseCase. Решил отказаться
    # @provide(scope=Scope.REQUEST)
    # async def uow(self, session_factory: async_sessionmaker[AsyncSession]) -> AsyncIterator[UnitOfWork]:
    #     async with SqlAlchemyUnitOfWork(session_factory=session_factory) as uow:
    #         yield uow

    @provide(scope=Scope.REQUEST)
    async def session(self, session_factory: async_sessionmaker[AsyncSession]) -> AsyncIterator[AsyncSession]:
        async with session_factory() as session:
            yield session

    uow = provide(SqlAlchemyUnitOfWork, provides=UnitOfWork, scope=Scope.REQUEST)


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
        DeleteCourseUseCase,
        DeleteLectureUseCase,
        DeleteSectionUseCase,
        DeleteModuleUseCase
    )
