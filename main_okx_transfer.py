import asyncio
import random
import warnings
from sys import stderr

from loguru import logger

from database.main import all_wallets_to_transfer
from main_zklending2 import _gas_check
from modules.okx_deposit import OkxDeposit

logger.remove()
custom_name = "MAIN Okx Transfer"
logger.add(stderr, format="<white>{time:HH:mm:ss}</white> | <level>{level: <8}</level> | "
                          "<cyan>{extra[action]:<15}</cyan> | <white>{message}</white>")
logger = logger.bind(action=custom_name)


async def okx_transfer(wallet: dict, index: int):
    logger.info(f"START    | index = {index} | {wallet['public_key']} |")
    await asyncio.sleep(int(0 + index * random.uniform(0.1, 0.1)) * 60)
    start = OkxDeposit(wallet=wallet, index=index)
    await start.transfer()


async def multithreading(limit: int, offset: int = 0):
    wallets = await all_wallets_to_transfer(limit=limit, offset=offset)

    tasks = []
    for index, wallet in enumerate(wallets):
        task = asyncio.create_task(okx_transfer(wallet=wallet, index=index))
        tasks.append(task)

    while len(tasks) > 0:
        tasks[:] = [task for task in tasks if not task.done()]
        await asyncio.sleep(60)


if __name__ == '__main__':
    warnings.filterwarnings("ignore")
    try:
        asyncio.run(multithreading(100, 0))
    except KeyboardInterrupt:
        pass
