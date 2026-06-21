from sqlmodel import SQLModel, Session, create_engine
from app.core.config import get_settings

engine = create_engine(get_settings().database_url, connect_args={"check_same_thread": False} if get_settings().database_url.startswith("sqlite") else {})

def init_db():
    SQLModel.metadata.create_all(engine)

def get_session():
    with Session(engine) as session:
        yield session
