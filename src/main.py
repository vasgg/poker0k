import asyncio
from contextlib import asynccontextmanager
import json
import logging.config
from pathlib import Path

from fastapi import FastAPI, HTTPException, Request
import pyautogui
from redis.asyncio import Redis
from uvicorn import Config, Server

from config import get_logging_config, settings
from controllers.crypt import Crypt
from task_model import Task


@asynccontextmanager
async def lifespan(webapp: FastAPI):
    redis_client = Redis(db=10)
    try:
        webapp.state.redis_client = redis_client
        yield
    finally:
        await redis_client.aclose()


app = FastAPI(lifespan=lifespan)


@app.post("/add_task/")
async def add_task(request: Request):
    data = await request.json()
    task = Task(**data)
    # headers_dict = request.headers
    # cryptor = Crypt(settings.key_encrypt, settings.key_decrypt)
    # signature = cryptor.decrypt(headers_dict['x-simpleex-sign'])
    # task_dict = json.loads(signature)
    # logging.info(f"Received new task: {task}, signature: {task_dict}")
    # if task_dict != data or task.status != 0:
    #     return {'status': False}
    try:
        redis_client = request.app.state.redis_client
        await redis_client.lpush('queue', task.json())
        logging.info(f"Task added to queue: {task.json()}")
        queue_length = await redis_client.llen('queue')
        logging.info(f"Current queue length: {queue_length}")
        return {'status': 'true'}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/get_task/")
async def get_task(request: Request):
    data = await request.json()
    headers_dict = request.headers
    cryptor = Crypt(settings.key_encrypt, settings.key_decrypt)
    signature = cryptor.decrypt(headers_dict['x-simpleex-sign'])
    task_dict = json.loads(signature)
    if task_dict != data:
        return {'status': False}
    redis_client = request.app.state.redis_client
    task_data = await redis_client.hget("tasks", data['order_id'])
    if not task_data:
        return {'status': False}
    task = json.loads(task_data.decode('utf-8'))
    logging.info(f"Requested task: {task}")
    return task


@app.post("/queue_length/")
async def queue_status(request: Request):
    data = await request.json()
    headers_dict = request.headers
    cryptor = Crypt(settings.key_encrypt, settings.key_decrypt)
    signature = cryptor.decrypt(headers_dict['x-simpleex-sign'])
    task_dict = json.loads(signature)
    screen_width, screen_height = pyautogui.size()
    if task_dict != data:
        return {'status': False}
    redis_client = request.app.state.redis_client
    queue_length = await redis_client.llen('queue')
    logging.info(f"Requested queue length: {queue_length}")
    return {
        "queue_count": queue_length,
        'resolution': f'{screen_width}x{screen_height}',
    }


async def main():
    logs_directory = Path("logs")
    screenshots_directory = Path("screenshots")
    logs_directory.mkdir(parents=True, exist_ok=True)
    screenshots_directory.mkdir(parents=True, exist_ok=True)
    logging_config = get_logging_config('pokerok')
    logging.config.dictConfig(logging_config)
    logging.info("server started...")

    config = Config(app=app, host="0.0.0.0", port=8800)
    server = Server(config)

    await server.serve()


def run_main():
    asyncio.run(main())


if __name__ == '__main__':
    run_main()
