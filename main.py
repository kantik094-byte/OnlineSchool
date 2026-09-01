from fastapi import FastAPI

from app.infrastructure.config import get_settings


def create_app() -> FastAPI:
    settings = get_settings()

    app = FastAPI(
        title=settings.api.title,
        debug=settings.api.debug,
    )
    return app


app = create_app()
