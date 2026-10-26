from collections.abc import AsyncIterator
from types import SimpleNamespace
from uuid import uuid4

import pytest
import pytest_asyncio
from dishka import Provider, Scope, from_context
from httpx import ASGITransport, AsyncClient
from sqlalchemy import delete
from sqlalchemy.ext.asyncio import AsyncEngine, AsyncSession, async_sessionmaker

from app.infrastructure.database.engine import build_engine
from app.infrastructure.database.models import (
    Base,
    CourseModel,
    LectureModel,
    ModuleModel,
    SectionModel,
    UserModel,
)
from app.infrastructure.security.password_hasher import PwdlibPasswordHasher
from main import create_app, create_container

PASSWORD = 'strongpassword123'


class TestDatabaseProvider(Provider):
    """Перекрывает фабрику сессий из DatabaseProvider: её передаёт тест через context."""

    session_factory = from_context(provides=async_sessionmaker[AsyncSession], scope=Scope.APP)


@pytest_asyncio.fixture(scope='session')
async def test_engine(tmp_path_factory) -> AsyncIterator[AsyncEngine]:
    database_path = tmp_path_factory.mktemp('test_db') / 'test_fastapi_education.db'
    engine = build_engine(f'sqlite+aiosqlite:///{database_path}')
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield engine
    await engine.dispose()


@pytest.fixture
def session_factory(test_engine) -> async_sessionmaker[AsyncSession]:
    return async_sessionmaker(bind=test_engine, expire_on_commit=False)


@pytest_asyncio.fixture
async def app(session_factory):
    container = create_container(
        TestDatabaseProvider(),
        context={async_sessionmaker[AsyncSession]: session_factory},
    )
    yield create_app(container)
    await container.close()


@pytest_asyncio.fixture
async def client(app) -> AsyncIterator[AsyncClient]:
    async with AsyncClient(transport=ASGITransport(app=app), base_url='http://test') as client:
        yield client


@pytest_asyncio.fixture(autouse=True)
async def clear_database(session_factory) -> None:
    async with session_factory() as session:
        for model in [LectureModel, SectionModel, ModuleModel, CourseModel, UserModel]:
            await session.execute(delete(model))
        await session.commit()


@pytest_asyncio.fixture
async def seeded_course_tree(session_factory):
    ids = SimpleNamespace(course_id=str(uuid4()), module_id=str(uuid4()), section_id=str(uuid4()), lecture_id=str(uuid4()), course_title='FastAPI course',
                          lecture_content='Lecture content')
    async with session_factory() as session:
        session.add_all([
            CourseModel(id=ids.course_id, title='FastAPI course', description='Clean architecture in practice.'),
            ModuleModel(id=ids.module_id, course_id=ids.course_id, title='MVP stage', description='Content.', position=1),
            SectionModel(id=ids.section_id, module_id=ids.module_id, title='Auth section', description='JWT.', position=1),
            LectureModel(id=ids.lecture_id, section_id=ids.section_id, title='Bearer token', content='Lecture content', position=1),
        ])
        await session.commit()
    return ids


async def _seed_user(session_factory, email: str, role: str) -> UserModel:
    async with session_factory() as session:
        user = UserModel(id=str(uuid4()), email=email, hashed_password=PwdlibPasswordHasher().hash(PASSWORD), role=role)
        session.add(user)
        await session.commit()
        return user


@pytest_asyncio.fixture
async def seeded_student_user(session_factory):
    return await _seed_user(session_factory, 'student@example.com', 'student')


@pytest_asyncio.fixture
async def seeded_admin_user(session_factory):
    return await _seed_user(session_factory, 'admin@example.com', 'admin')


async def _login(client: AsyncClient, email: str) -> dict[str, str]:
    response = await client.post('/api/auth/login', json={'email': email, 'password': PASSWORD})
    assert response.status_code == 200, response.text
    return {'Authorization': f"Bearer {response.json()['access_token']}"}


@pytest_asyncio.fixture
async def student_auth_headers(client, seeded_student_user):
    return await _login(client, seeded_student_user.email)


@pytest_asyncio.fixture
async def admin_auth_headers(client, seeded_admin_user):
    return await _login(client, seeded_admin_user.email)