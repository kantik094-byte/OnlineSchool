from sqlalchemy import event
from sqlalchemy.ext.asyncio import AsyncEngine, create_async_engine


def build_engine(url: str, echo: bool = False) -> AsyncEngine:
    """Единая точка создания engine: и для приложения, и для тестов."""
    engine = create_async_engine(url, echo=echo)
    if engine.dialect.name == 'sqlite':
        # В SQLite внешние ключи (и ondelete="CASCADE") по умолчанию выключены
        event.listen(engine.sync_engine, 'connect', _enable_sqlite_foreign_keys)
    return engine


def _enable_sqlite_foreign_keys(dbapi_connection, _connection_record) -> None:
    """Включает проверку внешних ключей в SQLite."""
    dbapi_connection.execute('PRAGMA foreign_keys=ON')