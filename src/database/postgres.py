from sqlmodel import Session, create_engine

from core.settings import settings


engine = create_engine(settings.database_string, echo=False, pool_pre_ping=True)


def get_sync_session() -> Session:
    return Session(engine)
