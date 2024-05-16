import asyncio
from contextlib import asynccontextmanager
import logging.config
from pathlib import Path

from fastapi import Depends, FastAPI, HTTPException
from redis.asyncio import Redis
from uvicorn import Config, Server

from config import get_logging_config
from enums import Task


@asynccontextmanager
async def lifespan(app: FastAPI):
    redis_client = Redis(db=10)
    try:
        yield redis_client
    finally:
        await redis_client.close()


app = FastAPI(lifespan=lifespan)


async def get_redis_client(redis_client: Redis = Depends(lifespan)):
    return redis_client


@app.post("/add_task/")
async def add_task(data):
    try:
        task_data = data.json()
        logging.info(f"Incoming data: {task_data}")
        return {"message": "Data received"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# @app.post("/add_task/")
# async def add_task(task: Task, redis_client: Redis = Depends(get_redis_client)):
#     try:
#         task_data = task.json()
#         await redis_client.publish('tasks', task_data)
#         logging.info(f"Task added to queue: {task_data}")
#         return {"message": "Task added to queue"}
#     except Exception as e:
#         raise HTTPException(status_code=500, detail=str(e))


async def main():
    logs_directory = Path("logs")
    screenshots_directory = Path("screenshots")
    logs_directory.mkdir(parents=True, exist_ok=True)
    screenshots_directory.mkdir(parents=True, exist_ok=True)
    logging_config = get_logging_config('pokerok')
    logging.config.dictConfig(logging_config)
    logging.info("app started...")

    config = Config(app=app, host="0.0.0.0", port=8800)
    server = Server(config)

    await server.serve()


def run_main():
    asyncio.run(main())


if __name__ == '__main__':
    run_main()
