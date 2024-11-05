import asyncio
import random
import warnings
from sys import stderr

from loguru import logger

from database.main import all_wallets_to_action, current_wallet
from main_zklending2 import _gas_check
from modules.dmail import Dmail
from modules.mintNft import *

logger.remove()
custom_name = "MAIN Action"
logger.add(stderr, format="<white>{time:HH:mm:ss}</white> | <level>{level: <8}</level> | "
                          "<cyan>{extra[action]:<15}</cyan> | <white>{message}</white>")
logger = logger.bind(action=custom_name)


class RandomAction:
    def __init__(self, wallet: dict,  index: int = 0,  minuts: [int, float] = 0) -> None:
        self.__wallet = wallet
        self.__index = index
        self.__minuts = minuts

    async def action(self):
        TYPE = [0, 1, 2]
        # TYPE = [0, 2]
        # TYPE = []

        if self.__wallet['mint_count'] == 0 \
                or ((0 in self.__wallet['nft_id']) and len(set(self.__wallet['nft_id'])) == 1):
            TYPE.append(0)
        if self.__wallet['message_count'] == 0:
            TYPE.append(1)
        if 0 not in self.__wallet['nft_id']:
            TYPE.append(2)

        if len(TYPE) == 0:
            logger.debug(f"FINISH NO ACTION  | index = {self.__index} | {self.__wallet['public_key']}")
            return

        _type = random.choice(TYPE)

        if _type == 0:
            await self._mint_starknet_id()
        elif _type == 1:
            await self._mail()
        elif _type == 2:
            await self._mint_starkverse_art()
        else:
            logger.debug(f"FINISH NO ACTION  | index = {self.__index} | {self.__wallet['public_key']}")
            return

    async def _mint_starknet_id(self):
        start = StarkNetId(wallet=self.__wallet, index=self.__index, minuts=self.__minuts)
        await start.mint()

    async def _mint_starkverse_art(self):
        start = StarkverseArt(wallet=self.__wallet, index=self.__index, minuts=self.__minuts)
        await start.mint()

    async def _mail(self):
        start = Dmail(wallet=self.__wallet, index=self.__index, minuts=self.__minuts)
        await start.mail()


async def one_wallet_swaps(wallet: dict, index: int):
    num_of_action = random.randint(1, 2)
    logger.info(f"START ACTION  | index = {index} | {wallet['public_key']} | {num_of_action}")
    await asyncio.sleep(int(0 + index * random.uniform(3, 3)) * 60)

    for num in range(num_of_action):
        await _gas_check()
        start = RandomAction(wallet=wallet, index=index, minuts=random.randint(5, 5))
        await start.action()
        wallet = await current_wallet(public_key=wallet['public_key'])

    logger.success(f"FINISH ACTION | index = {index} | {wallet['public_key']} | {num_of_action}")


async def multithreading(limit: int, offset: int = 0):
    wallets = await all_wallets_to_action(limit=limit, offset=offset)
    random.shuffle(wallets)
    random.shuffle(wallets)
    random.shuffle(wallets)

    tasks = []
    for index, wallet in enumerate(wallets):
        task = asyncio.create_task(one_wallet_swaps(wallet=wallet, index=index))
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
