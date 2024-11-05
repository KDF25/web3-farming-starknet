import asyncio
import warnings
from sys import stderr

from loguru import logger

from constants.data import STARKNET, ALL_TOKENS
from database.main import *
from modules.utils import get_account, get_from_token_contract

logger.remove()
custom_name = "All tokens checker"
logger.add(stderr, format="<white>{time:HH:mm:ss}</white> | <level>{level: <8}</level> | "
                          "<cyan>{extra[action]:<15}</cyan> | <white>{message}</white>")
logger = logger.bind(action=custom_name)


class AllTokensChecker:
    def __init__(self, wallet: dict, index: int = 0) -> None:
        self.__account = None
        self.__wallet = wallet
        self.__index = index

    async def checker(self):
        try:

            logger.info(f'START  token checker | index = {self.__index} | id = {self.__wallet["id"]} | {self.__wallet["public_key"]}')
            self.__account, session = await get_account(wallet=self.__wallet)
            old_tokens = self.__wallet["Tokens"]
            TOKENS = []
            all_tokens = {}
            for token in ALL_TOKENS:
                while True:
                    try:
                        token_address = int(STARKNET[token], 16)
                        token_contract = await get_from_token_contract(account=self.__account, from_token=token,address=token_address)

                        token_decimals = await token_contract.functions['decimals'].call()
                        token_balance = await token_contract.functions['balanceOf'].prepare(account=self.__account.address).call()

                        token_balance = token_balance[0]
                        token_decimals = token_decimals[0]

                        if token_balance != 0 and token not in ["USDT", "USDC", "DAI"]:
                            TOKENS.append(token)
                            logger.error(f'TOKEN = {token} | index = {self.__index} | {self.__wallet["public_key"]} | Balance = {token_balance / 10 ** token_decimals} {token} |')
                        if token_balance >= 1 * 10 ** token_decimals and token in ["USDT", "USDC", "DAI"]:
                            TOKENS.append(token)
                            logger.error(f'TOKEN = {token} | index = {self.__index} | {self.__wallet["public_key"]} | Balance = {token_balance / 10 ** token_decimals} {token} |')
                        elif token_balance / (10 ** token_decimals) * 70000 > 1 and token == "WBTC":
                            TOKENS.append(token)
                            logger.error(f'TOKEN = {token} | index = {self.__index} | {self.__wallet["public_key"]} | Balance = {token_balance / 10 ** token_decimals} {token} |')
                        elif token_balance / (10 ** token_decimals) * 4000 > 1 and token in ["ETH", "zETH"]:
                            TOKENS.append(token)
                            logger.error(f'TOKEN = {token} | index = {self.__index} | {self.__wallet["public_key"]} | Balance = {token_balance / 10 ** token_decimals} {token} |')

                        all_tokens.update({token: token_balance / 10 ** token_decimals})

                        break
                    except Exception:
                        pass
            # await update_all_tokens(public_key=self.__wallet['public_key'], TOKENS=TOKENS, comment="checked_tokens")
            await session.close()
            logger.success(f'FINISH  token checker | index = {self.__index} | {self.__wallet["public_key"]} | \n {all_tokens}')

            if len(set(TOKENS) - set(old_tokens)) == 0:
                logger.success(f'FINISH  token checker | index = {self.__index} | {self.__wallet["public_key"]} | TOKENS = {TOKENS} \t\t OLD = {old_tokens}\n\n')
            else:
                logger.debug(f'FINISH  token checker | index = {self.__index} | {self.__wallet["public_key"]} | TOKENS = {TOKENS} \t\t OLD = {old_tokens}\n')

        except Exception as ex:
            await session.close()
            logger.error(f'ERROR  token checker | index = {self.__index} | {self.__wallet["public_key"]} | {ex}')


async def new(wallet: dict, index: int = 0):
    check = AllTokensChecker(
        wallet=wallet,
        index=index
    )
    await check.checker()


async def multithreading(limit: int, offset: int = 0):
    wallets = await all_wallets_to_check(limit=limit, offset=offset)

    for index, wallet in enumerate(wallets):
        await new(wallet=wallet, index=index)


if __name__ == '__main__':
    warnings.filterwarnings("ignore")
    try:
        logger.info(f'START check')
        asyncio.run(multithreading(limit=100, offset=130))
    except KeyboardInterrupt:
        pass

