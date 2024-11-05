import asyncio
import copy
import random
import warnings
from sys import stderr

from loguru import logger

from constants.data import *
from database.main import all_wallets_to_swap, current_wallet
from modules.swaps import *

logger.remove()
custom_name = "MAIN Swap"
logger.add(stderr, format="<white>{time:HH:mm:ss}</white> | <level>{level: <8}</level> | "
                          "<cyan>{extra[action]:<15}</cyan> | <white>{message}</white>")
logger = logger.bind(action=custom_name)

SELL_TO_TOKEN = ["ETH"]
NUM_OF_TOKENS = 4
ORDER_TYPE = ["sell",
              # "buy"
              ]
MAX_AMOUNT = int(10 ** 200)


class RandomSwaps:
    def __init__(self, wallet: dict,  index: int = 0,  minuts: [int, float] = 0) -> None:
        self._Swap = None
        self.__from_token = None
        self.__eth_equivalent = round(random.uniform(1, 1.25) * 0.01, 4)
        self.__wallet = wallet
        self.__private_key = wallet["private_key"]
        self.__Tokens = wallet["Tokens"]
        self.__order = random.choice(ORDER_TYPE)
        self.__index = index
        self.__minuts = minuts

    async def _get_amount(self, SWAP_TOKENS: list):
        try:
            tokens = list(set(SWAP_TOKENS) - set(self.__Tokens))
            self.__to_token = random.choice(tokens)
            self.__amount = self.__eth_equivalent

        except Exception as ex:
            logger.error(f"TOKENS ERROR    | index = {self.__index} | {self.__wallet['public_key']} | SWAP_TOKENS = {SWAP_TOKENS} | TOKENS = {self.__Tokens} | {ex}")

    async def start_swaps(self):

        if len(self.__Tokens) == 1 or (len(self.__Tokens) < NUM_OF_TOKENS and self.__order == "buy"):
            # random - buy on random DEX it random token for eth equivalent
            await self._buy_token()

        elif len(self.__Tokens) >= NUM_OF_TOKENS or self.__order == "sell":
            # only sell token all currency except ETH for ETH or USDC
            await self._sell_token()

        else:
            return

        await self._choose_dex()

    async def _buy_token(self):
        self.__from_token = "ETH"
        DEX = [1, 2, 3, 5, 6, 7]
        self.__dex = random.choice(DEX)

        if self.__dex == 1:
            await self._get_amount(MYSWAP_TOKENS)

        elif self.__dex == 2:
            await self._get_amount(JEDISWAP_TOKENS)

        elif self.__dex == 3:
            await self._get_amount(TENKSWAP_TOKENS)

        elif self.__dex == 4:
            await self._get_amount(ANVUSWAP_TOKENS)

        elif self.__dex == 5:
            await self._get_amount(SITHSWAP_TOKENS)

        elif self.__dex == 6:
            await self._get_amount(STARKEXSWAP_TOKENS)

        elif self.__dex == 7:
            await self._get_amount(FIRBOUSSWAP_TOKENS)

    async def _sell_token(self):
        Random = []
        try:
            self.__Tokens.remove("ETH")
        except Exception:
            pass

        self.__from_token = random.choice(self.__Tokens)
        sell_to_token = copy.deepcopy(SELL_TO_TOKEN)

        try:
            sell_to_token.remove(self.__from_token)
        except Exception:
            pass

        self.__to_token = random.choice(sell_to_token)
        self.__amount = MAX_AMOUNT

        if self.__from_token in MYSWAP_TOKENS:
            Random.append(1)

        if self.__from_token in JEDISWAP_TOKENS:
            Random.append(2)

        if self.__from_token in TENKSWAP_TOKENS:
            Random.append(3)

        # if self.__from_token in ANVUSWAP_TOKENS:
        #     Random.append(4)

        if self.__from_token in SITHSWAP_TOKENS:
            Random.append(5)

        if self.__from_token in STARKEXSWAP_TOKENS:
            Random.append(6)

        if self.__from_token in FIRBOUSSWAP_TOKENS:
            Random.append(7)

        # self.__dex = random.choice(Random)
        self.__dex = 2

    async def _choose_dex(self):
        if self.__dex == 1:
            Swap = MySwap(wallet=self.__wallet, index=self.__index, minuts=self.__minuts,
                          from_token=self.__from_token, to_token=self.__to_token, amount=self.__amount)

        elif self.__dex == 2:
            Swap = JediSwap(wallet=self.__wallet, index=self.__index, minuts=self.__minuts,
                            from_token=self.__from_token, to_token=self.__to_token, amount=self.__amount)

        elif self.__dex == 3:
            Swap = TenKSwap(wallet=self.__wallet, index=self.__index, minuts=self.__minuts,
                            from_token=self.__from_token, to_token=self.__to_token, amount=self.__amount)

        elif self.__dex == 4:
            Swap = AnvuSwap(wallet=self.__wallet, index=self.__index, minuts=self.__minuts,
                            from_token=self.__from_token, to_token=self.__to_token, amount=self.__amount)

        elif self.__dex == 5:
            Swap = SithSwap(wallet=self.__wallet, index=self.__index, minuts=self.__minuts,
                            from_token=self.__from_token, to_token=self.__to_token, amount=self.__amount)

        elif self.__dex == 6:
            Swap = StarkExSwap(wallet=self.__wallet, index=self.__index, minuts=self.__minuts,
                               from_token=self.__from_token, to_token=self.__to_token, amount=self.__amount)

        elif self.__dex == 7:
            Swap = FibrousSwap(wallet=self.__wallet, index=self.__index, minuts=self.__minuts,
                               from_token=self.__from_token, to_token=self.__to_token, amount=self.__amount)

        else:
            return

        await Swap.swap()


async def one_wallet_swaps(wallet: dict, index: int):
    num_of_swaps = len(wallet['Tokens']) - 1
    logger.info(f"SWAPS | index = {index} | {wallet['public_key']} | num = {num_of_swaps} |")
    if num_of_swaps == 0:
        return
    await asyncio.sleep(int(0 + index * random.uniform(0.05, 0.05)) * 10)

    for num in range(num_of_swaps):
        start = RandomSwaps(wallet=wallet, index=index, minuts=0)
        await start.start_swaps()
        wallet = await current_wallet(public_key=wallet['public_key'])

    logger.success(f"FINISH SWAPS    | index = {index} | {wallet['public_key']} |  num = {num_of_swaps} | ")


async def multithreading(limit: int, offset: int = 0):
    wallets = await all_wallets_to_swap(limit=limit, offset=offset)
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
        asyncio.run(multithreading(140, 0))
    except KeyboardInterrupt:
        pass
