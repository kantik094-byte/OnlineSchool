import uvicorn
from dishka import make_async_container
from dishka.integrations.fastapi import setup_dishka, FastapiProvider
from fastapi import FastAPI

from app.infrastructure.config import get_settings
from app.presentation.api.handlers import register_exception_handlers
from app.presentation.api.routes import router as api_router
from app.di.providers import AuthProvider, ConfigProvider, DatabaseProvider, SecurityProvider, UseCasesProvider


def create_app() -> FastAPI:
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

    container = make_async_container(
        ConfigProvider(),      # Settings, DatabaseSettings, JwtSettings
        DatabaseProvider(),    # session_factory, UnitOfWork, репозитории
        SecurityProvider(),    # PasswordHasher, TokenService
        UseCasesProvider(),    # все use case'ы
        AuthProvider(),        # IdentityProvider
        FastapiProvider(),
    )

    setup_dishka(container, app)
    app.include_router(api_router)
    return app


app = create_app()

if __name__ == "__main__":
    uvicorn.run("main:app", host="127.0.0.1", port=8000, reload=True)