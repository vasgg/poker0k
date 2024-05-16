import logging

import aiohttp

logger = logging.getLogger(__name__)


async def send_report(nickname: str, amount: int) -> None:
    async with aiohttp.ClientSession() as session:
        url = ''
        data = {
            "order_id": 123,
            "user_id": 123,
            "requisite": "pokermaster",
            "amount": 5000.00,
            "status": 0,  # 0 - Not payed | 1 - Payed
        }
        text_ok = f'Transfer to: {nickname}, amount: ${amount}, status: SUCCESS'
        text_error = f'Transfer to: {nickname}, amount: ${amount}, status: FAILED: ' + '{}. {}'

    async with session.post(url, json=data) as response:
        if response.status == 200:
            logger.info(text_ok)
        else:
            error_text = await response.text()
            logger.info(text_error.format(response.status, error_text))
