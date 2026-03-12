from sqlmodel import SQLModel, create_engine, Session
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker

# MySQL 异步连接字符串格式：mysql+aiomysql://users:password@host:port/dbname
DATABASE_URL = "mysql+aiomysql://root:123456@localhost:3306/rag_agent"

# 创建异步引擎
async_engine = create_async_engine(DATABASE_URL, echo=True, pool_pre_ping=True)

# 创建异步会话工厂
async_session_maker = sessionmaker(async_engine, class_=AsyncSession, expire_on_commit=False)

# 依赖注入：获取 DB Session
async def get_session():
    async with async_session_maker() as session:
        yield session