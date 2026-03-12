from contextlib import asynccontextmanager

from fastapi import FastAPI
from sqlmodel import SQLModel
from starlette.middleware.cors import CORSMiddleware

from api.database.config import async_engine
from api.router.file.index import file_router
import uvicorn

from api.router.users.index import user_router


# 定义 lifespan 上下文管理器
@asynccontextmanager
async def lifespan(app: FastAPI):
    # === Startup ===
    print("🚀 Application startup...")
    # 开发环境：自动创建表（生产环境请用 Alembic）
    async with async_engine.begin() as conn:
        await conn.run_sync(SQLModel.metadata.create_all)

    yield  # 👈 应用运行期间

    # === Shutdown ===
    print("🛑 Application shutdown...")
    await async_engine.dispose()  # 关闭数据库连接池


app = FastAPI(lifespan=lifespan)


app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 允许的前端地址
    allow_credentials=True,
    allow_methods=["*"],  # 允许所有 HTTP 方法
    allow_headers=["*"],  # 允许所有 Headers
)


app.include_router(router=file_router)
app.include_router(router=user_router)

if __name__ == "__main__":
    uvicorn.run(app, host="127.0.0.1", port=1016)