import asyncio
from datetime import datetime
import logging.config

import redis.asyncio as redis
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column
from sqlalchemy import DateTime, String, func

from config import get_logging_config, settings
from internal import Task

DB_URL = f"mysql+aiomysql://{settings.DB_USER}:{settings.DB_PASSWORD.get_secret_value()}@{settings.DB_HOST}:{settings.DB_PORT}/{settings.DB_NAME}"
engine = create_async_engine(DB_URL, echo=True)
AsyncSessionLocal = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False
)


class Base(DeclarativeBase):
    __abstract__ = True
    id: Mapped[int] = mapped_column(primary_key=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class Report(Base):
    __tablename__ = 'reports'

    order_id: Mapped[int]
    user_id: Mapped[int]
    requisite: Mapped[str] = mapped_column(String(100))
    amount: Mapped[float]
    status: Mapped[int]
    callback_url: Mapped[str] = mapped_column(String(200))


async def insert_record_to_db(task: Task):
    try:
        async with AsyncSessionLocal() as db_session:
            async with db_session.begin():
                record = Report(
                    order_id=task.order_id,
                    user_id=task.user_id,
                    requisite=task.requisite,
                    amount=task.amount,
                    status=task.status,
                    callback_url=task.callback_url
                )
                db_session.add(record)
                await db_session.flush()
        logging.info(f"Record {record.id} inserted successfully. Task id: {task.order_id}, requisite: {task.requisite}, amount: {task.amount}")
    except Exception as e:
        logging.exception(f"Error interacting with the database: {e}")


async def init_db():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all, checkfirst=True)


async def main():
    logging_config = get_logging_config('reporter')
    logging.config.dictConfig(logging_config)
    redis_client = redis.Redis(db=10)
    logging.info('Reporter started...')
    while True:
        # noinspection PyTypeChecker
        record_data = await redis_client.brpop('records', timeout=5)
        if record_data:
            _, record_data = record_data
            record = Task.model_validate_json(record_data.decode('utf-8'))
            await insert_record_to_db(record)


def run_main():
    asyncio.run(main())


if __name__ == '__main__':
    run_main()
