import asyncio
import random
import warnings
from sys import stderr

from loguru import logger
from web3 import HTTPProvider, Web3

from database.main import current_wallet, all_wallets_to_lending
from modules.utils import check_token_balance
from modules.zkLend import *
from modules.swaps import *

logger.remove()
custom_name = "MAIN ZkLending"
logger.add(stderr, format="<white>{time:HH:mm:ss}</white> | <level>{level: <8}</level> | "
                          "<cyan>{extra[action]:<15}</cyan> | <white>{message}</white>")
logger = logger.bind(action=custom_name)

# BORROW_TOKEN = ["ETH", "USDC", "USDT"]
BORROW_TOKEN = ["ETH"]
TYPE = ["REPAY", "NO_REPAY"]
# TYPE = ["REPAY"]
ETH_VOLUME = 1 * 10 ** 18
GAS_MAX = 60


async def _gas():
    while True:
        try:
            mainnet_w3 = Web3(HTTPProvider(endpoint_uri='https://eth.meowrpc.com'))
            return int(mainnet_w3.eth.gas_price / 10 ** 9)
        except Exception:
            pass


async def _gas_check() -> bool:
    while True:
        gas = await _gas()
        if gas > GAS_MAX:
            logger.info(f"GAS = {gas} GWEI")
            await asyncio.sleep(random.uniform(2, 5) * 60)
        else:
            return True


class RandomSwaps:
    def __init__(self, wallet: dict, from_token: str, to_token: str, index: int = 0, minuts: [int, float] = 0) -> None:
        self.__from_token = from_token
        self.__to_token = to_token
        self.__amount = round(random.uniform(1, 1.25) * 3 / 1700, 4)
        self.__wallet = wallet
        self.__private_key = wallet["private_key"]
        self.__Tokens = wallet["Tokens"]
        self.__index = index
        self.__minuts = minuts

    async def start(self):
        logger.info(f"GETTOKEN | index = {self.__index} | {self.__wallet['public_key']} |")
        DEX = [1, 2, 3, 5, 6, 7]
        dex = random.choice(DEX)

        if dex == 1:
            Swap = MySwap(wallet=self.__wallet, index=self.__index, minuts=self.__minuts,
                          from_token=self.__from_token, to_token=self.__to_token, amount=self.__amount)

        elif dex == 2:
            Swap = JediSwap(wallet=self.__wallet, index=self.__index, minuts=self.__minuts,
                            from_token=self.__from_token, to_token=self.__to_token, amount=self.__amount)

        elif dex == 3:
            Swap = TenKSwap(wallet=self.__wallet, index=self.__index, minuts=self.__minuts,
                            from_token=self.__from_token, to_token=self.__to_token, amount=self.__amount)

        elif dex == 4:
            Swap = AnvuSwap(wallet=self.__wallet, index=self.__index, minuts=self.__minuts,
                            from_token=self.__from_token, to_token=self.__to_token, amount=self.__amount)

        elif dex == 5:
            Swap = SithSwap(wallet=self.__wallet, index=self.__index, minuts=self.__minuts,
                            from_token=self.__from_token, to_token=self.__to_token, amount=self.__amount)

        elif dex == 6:
            Swap = StarkExSwap(wallet=self.__wallet, index=self.__index, minuts=self.__minuts,
                               from_token=self.__from_token, to_token=self.__to_token, amount=self.__amount)

        elif dex == 7:
            Swap = FibrousSwap(wallet=self.__wallet, index=self.__index, minuts=self.__minuts,
                               from_token=self.__from_token, to_token=self.__to_token, amount=self.__amount)

        else:
            return

        await Swap.swap()





class Lending:

    def __init__(self, wallet: dict, _type: str, borrow_token: str, index: int = 0, minuts: [int, float] = 0) -> None:
        self.__type = _type
        self.__borrow_token = borrow_token
        self.__wallet = wallet
        self.__index = index
        self.__minuts = minuts

    async def start(self):
        # await self._check_borrow_token()
        await _gas_check()
        deposit = ZkLendDeposit(wallet=self.__wallet, from_token="ETH", index=self.__index,
                                minuts=random.randint(5, 20))
        await deposit.start()
        wallet = await current_wallet(public_key=self.__wallet['public_key'])

        if self.__type == "REPAY":
            await _gas_check()
            borrow = ZkLendBorrow(wallet=wallet, from_token="ETH", to_token=self.__borrow_token, index=self.__index,
                                  minuts=random.randint(5, 20))
            await borrow.start()
            wallet = await current_wallet(public_key=wallet['public_key'])

            await _gas_check()
            repay = ZkLendRepayAll(wallet=wallet, token=self.__borrow_token, index=self.__index,
                                   minuts=random.randint(5, 20))
            await repay.start()
            wallet = await current_wallet(public_key=wallet['public_key'])

        await _gas_check()
        withdraw = ZkLendWithdraw(wallet=wallet, token="ETH", index=self.__index)
        await withdraw.start()
        await asyncio.sleep(self.__minuts * 60)

    async def _check_borrow_token(self):
        if self.__borrow_token != "ETH" and self.__type == "REPAY":
            token_balance, token_decimals = await check_token_balance(wallet=self.__wallet, token=self.__borrow_token)

        else:
            return

        if token_balance <= 0.2 * 10 ** token_decimals:
            swap = RandomSwaps(wallet=self.__wallet, from_token="ETH", to_token=self.__borrow_token,
                               index=self.__index, minuts=random.randint(3, 10))
            await swap.start()


async def one_wallet_lending(wallet: dict, index: int):
    _type = random.choice(TYPE)
    borrow_token = random.choice(BORROW_TOKEN)
    logger.info(f"LENDING  | index = {index} | {wallet['public_key']} | total volume = {round(wallet['zklend']['total_volume'] / 10 ** 18, 4)} ETH / {int(wallet['zklend']['total_volume'] / 10 ** 18 * 1650)} USD ||| {borrow_token} | {_type} |")
    await asyncio.sleep(int(0 + index * random.uniform(3, 10)) * 60)

    while wallet['zklend']["total_volume"] <= ETH_VOLUME:
        lending = Lending(wallet=wallet, _type=_type, borrow_token=borrow_token, index=index, minuts=random.randint(20, 30))
        await lending.start()
        wallet = await current_wallet(public_key=wallet['public_key'])
        _type = random.choice(TYPE)
        borrow_token = random.choice(BORROW_TOKEN)
        logger.info(f"LENDING  | index = {index} | {wallet['public_key']} | {borrow_token} | {_type}")

    logger.success(f"FINISH LENDING    | index = {index} | {wallet['public_key']} | total volume = {round(wallet['zklend']['total_volume'] / 10 ** 18, 4)} ETH / {int(wallet['zklend']['total_volume'] / 10 ** 18 * 1650)} USD ||| {borrow_token} | {_type} |")


async def multithreading(limit: int, offset: int = 0):
    wallets = await all_wallets_to_lending(limit=limit, offset=offset)
    random.shuffle(wallets)
    random.shuffle(wallets)
    random.shuffle(wallets)

    tasks = []
    for index, wallet in enumerate(wallets):
        wallet = await current_wallet(public_key=wallet)
        task = asyncio.create_task(one_wallet_lending(wallet=wallet, index=index))
        tasks.append(task)

    while len(tasks)>0:
        tasks[:] = [task for task in tasks if not task.done()]
        await asyncio.sleep(60)


if __name__ == '__main__':
    warnings.filterwarnings("ignore")
    try:
        asyncio.run(multithreading(15, 0))
    except KeyboardInterrupt:
        pass
