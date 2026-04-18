from contextlib import asynccontextmanager

import uvicorn
from fastapi import FastAPI
from sqlmodel import SQLModel
from starlette.middleware.cors import CORSMiddleware
from starlette.staticfiles import StaticFiles

from core.settings import settings
from service.bootstrap_admin import ensure_bootstrap_admin
from service.database.connect import async_engine
from service.router.agent.index import agent_router
from service.router.file.index import file_router, legacy_public_file_router
from service.router.role.index import role_router
from service.router.users.index import user_router


def create_server() -> FastAPI:
    settings.validate_runtime_config()

    @asynccontextmanager
    async def lifespan(app: FastAPI):
        print("Application startup...")
        if settings.database_auto_create:
            print("DATABASE_AUTO_CREATE is enabled. Using legacy create_all bootstrap.")
            async with async_engine.begin() as conn:
                await conn.run_sync(SQLModel.metadata.create_all)
        else:
            print("Database auto-create is disabled. Run `alembic upgrade head` before starting in a fresh environment.")

        await ensure_bootstrap_admin()

        yield

        print("Application shutdown...")
        await async_engine.dispose()

    app = FastAPI(lifespan=lifespan)

    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_allow_origins,
        allow_credentials=settings.cors_allow_credentials,
        allow_methods=settings.cors_allow_methods,
        allow_headers=settings.cors_allow_headers,
    )

    public_dir = settings.resolved_public_dir
    if settings.serve_public_files and public_dir.exists():
        app.mount(settings.normalized_public_url_path, StaticFiles(directory=str(public_dir)), name="public")

    app.include_router(router=file_router)
    app.include_router(router=legacy_public_file_router)
    app.include_router(router=agent_router)
    app.include_router(router=user_router)
    app.include_router(router=role_router)
    return app


if __name__ == "__main__":
    uvicorn.run(create_server(), host=settings.server_host, port=settings.server_port)
