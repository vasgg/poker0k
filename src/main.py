import asyncio
from contextlib import asynccontextmanager
import logging.config
from pathlib import Path

from fastapi import Depends, FastAPI, HTTPException, Request
from redis.asyncio import Redis
from uvicorn import Config, Server

from config import get_logging_config, settings
from controllers.crypt import Crypt


@asynccontextmanager
async def lifespan(webapp):
    redis_client = Redis(db=10)
    try:
        yield {"redis_client": redis_client}
    finally:
        await redis_client.aclose()


app = FastAPI(lifespan=lifespan)


def get_redis_client(app_state: dict = Depends(lifespan)):
    return app_state["redis_client"]


@app.post("/add_task/")
async def add_task(request: Request, redis_client: Redis = Depends(get_redis_client)):
    headers_dict = request.headers
    data = await request.json()
    cryptor = Crypt(settings.key_encrypt, settings.key_decrypt)
    check = cryptor.decrypt(headers_dict['x-simpleex-sign'])
    task = data.model_dump_json()
    logging.info(f"Received new task: {task}, signature: {check}")
    if check != task:
        return {"message": "Invalid signature"}
    if task.status != 0:
        return {"message": "Invalid status"}
    try:
        task_data = task.json()
        await redis_client.publish('tasks', task_data)
        logging.info(f"Task added to queue: {task_data}")
        return {"message": "Task added to queue"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/queue_length/")
async def queue_status(redis_client: Redis = Depends(get_redis_client)):
    queue_length = await redis_client.llen('tasks')
    return {"queue_count": queue_length}


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
