from collections.abc import AsyncGenerator
import datetime
import uuid


from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine, async_sessionmaker
from sqlalchemy.orm import DeclarativeBase, relationship
DATABASE_URL = "sqlite+aiosqlite:///./test.db"

class Base(DeclarativeBase):
    pass

class Post(Base):
    __tablename__ = "posts"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    caption = Column(String(255), nullable=False)
    url = Column(String(255), nullable=False)
    file_type = Column(String(50), nullable=False)
    file_name = Column(String(255), nullable=False)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)




engine = create_async_engine(DATABASE_URL, echo=True)
async_session = async_sessionmaker(engine, expire_on_commit=False)

async def create_db_and_tables():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

async def get_async_session() -> AsyncGenerator[AsyncSession, None]:
    async with async_session() as session:
        yield session