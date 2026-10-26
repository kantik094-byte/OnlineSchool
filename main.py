import uvicorn
from dishka import Provider, AsyncContainer
from dishka import make_async_container
from dishka.integrations.fastapi import setup_dishka, FastapiProvider
from fastapi import FastAPI

from app.di.providers import AuthProvider, ConfigProvider, DatabaseProvider, SecurityProvider, UseCasesProvider
from app.infrastructure.config import get_settings
from app.presentation.api.handlers import register_exception_handlers
from app.presentation.api.routes import router as api_router


def create_container(*overrides: Provider, context: dict | None = None) -> AsyncContainer:
    """Единственное место, где собирается граф зависимостей."""
    return make_async_container(
        ConfigProvider(),
        DatabaseProvider(),
        SecurityProvider(),
        UseCasesProvider(),
        AuthProvider(),
        FastapiProvider(),
        *overrides,          # тестовые провайдеры идут последними и перекрывают боевые
        context=context,
    )



def create_app(container: AsyncContainer | None = None) -> FastAPI:
    settings = get_settings()

    app = FastAPI(
        title=settings.api.title,
        debug=settings.api.debug,
        description=(
            "Online school API built with clean architecture. "
            "At the first stage, the application supports public content reading "
            "and administrative management of courses, modules, sections and lectures."
        ),
        version="1.0.0",
        openapi_tags=[
            {
                "name": "Content",
                "description": "Public endpoints for reading courses, course structure and lectures.",
            },
            {
                "name": "Admin",
                "description": "Administrative endpoints for creating and updating content.",
            },
            {
                'name': 'Auth',
                'description': 'Endpoints for user registration and login with JWT token issuing.',
            },
        ],
    )

    register_exception_handlers(app)
    setup_dishka(container or create_container(), app)
    app.include_router(api_router)
    return app


app = create_app()

if __name__ == "__main__":
    uvicorn.run("main:app", host="127.0.0.1", port=8000, reload=True)