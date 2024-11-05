import asyncio
import random
import warnings
from sys import stderr

from loguru import logger

from database.main import all_wallets_to_deploy
from modules.account import one_account_deploy_new

logger.remove()
custom_name = "MAIN New Deploy"
logger.add(stderr, format="<white>{time:HH:mm:ss}</white> | <level>{level: <8}</level> | "
                          "<cyan>{extra[action]:<15}</cyan> | <white>{message}</white>")
logger = logger.bind(action=custom_name)


async def one_wallet_deploy(wallet: dict, index: int):
    logger.info(f"START     | index = {index} | {wallet['public_key']} |")
    await asyncio.sleep(int(0 + index * random.uniform(8, 15)) * 60)
    await one_account_deploy_new(wallet=wallet, index=index)
    logger.success(f"FINISH   | index = {index} | {wallet['public_key']}")


async def multithreading(limit: int, offset: int = 0):
    wallets = await all_wallets_to_deploy(limit=limit, offset=offset)
    random.shuffle(wallets)
    random.shuffle(wallets)
    random.shuffle(wallets)

    tasks = []
    for index, wallet in enumerate(wallets):
        task = asyncio.create_task(one_wallet_deploy(wallet=wallet, index=index))
        tasks.append(task)

    while len(tasks) > 0:
        tasks[:] = [task for task in tasks if not task.done()]
        await asyncio.sleep(60)


if __name__ == '__main__':
    warnings.filterwarnings("ignore")
    try:
        asyncio.run(multithreading(30, 0))
    except KeyboardInterrupt:
        pass

