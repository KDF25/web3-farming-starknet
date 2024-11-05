import asyncio
from sys import stderr

from loguru import logger
from starknet_py.contract import Contract
from starknet_py.net.account.account import Account
from starknet_py.net.gateway_client import GatewayClient
from starknet_py.net.models import StarknetChainId
from starknet_py.net.signer.stark_curve_signer import KeyPair

from config import max_tries
from constants.data import STARKNET, starkverseart_abi

from database.main import update_mint_nft
from modules.utils import *

logger.remove()
custom_name = "StarkVerseArt"
logger.add(stderr, format="<white>{time:HH:mm:ss}</white> | <level>{level: <8}</level> | "
                          "<cyan>{extra[action]:<15}</cyan> | <white>{message}</white>")
logger = logger.bind(action=custom_name)


class StarkverseArt:
    def __init__(self, wallet: dict,  index: int = 0, minuts: [float, int] = 0) -> None:
        self.__wallet = wallet
        self.__account = None
        self.__index = index
        self.__minuts = minuts
        self.__repeat = 0

    async def mint(self):
        try:
            while True:
                try:
                    self.__account, session = await get_account(wallet=self.__wallet)
                    mint_router_address = int(STARKNET["starkverseart_router"], 16)
                    eth_contract = await get_from_token_contract(account=self.__account,
                                                                 from_token="ETH",
                                                                 address=int(STARKNET["ETH"], 16))

                    balance = await eth_contract.functions['balanceOf'].prepare(
                        account=self.__account.address
                    ).call()

                    balance = balance[0]
                    break

                except Exception as ex:
                    ex = str(ex).replace("\n", " - ")
                    await session.close()
                    logger.error(f'ERROR_1 |  index = {self.__index} | {self.__wallet["public_key"]} | {ex}')

            logger.info(f'START    |  index = {self.__index} | {self.__wallet["public_key"]} | Balance = {balance / 10 ** 18} ETH ')

            mint_contract = Contract(
                address=mint_router_address,
                provider=self.__account,
                abi=starkverseart_abi
            )

            mint_call = mint_contract.functions["publicMint"].prepare(to=self.__account.address)
            calls = mint_call

            try:
                response = await self.__account.execute(
                    calls=calls,
                    auto_estimate=True,
                )

            except Exception:
                response = await self.__account.execute(
                    calls=calls,
                    auto_estimate=True,
                    cairo_version=1
                )

            transaction = await self.__account.client.wait_for_tx(response.transaction_hash)
            tx_hash = hex(response.transaction_hash)

            logger.success(f'FINISH   |  index = {self.__index} | {self.__wallet["public_key"]} | Transaction: {STARKNET["voyager"]}/tx/{tx_hash} | SLEEP = {round(self.__minuts, 2)} min')
            await update_mint_nft(public_key=self.__wallet["public_key"], nft_id=0)
            await session.close()
            await asyncio.sleep(self.__minuts * 60)

        except Exception as ex:
            ex = str(ex).replace("\n", " - ")
            await session.close()
            logger.error(f'ERROR_3 |  index = {self.__index} | {self.__wallet["public_key"]} | {ex}')

            if self.__repeat < max_tries:
                await asyncio.sleep(5 * 60)
                self.__repeat += 1
                await self.mint()




async def main():
    wallet = {
        "public_key": "",
        "private_key": '',
        "current_message": "",
        "current_mail": "",
    }
    start = StarkverseArt(wallet=wallet)
    await start.mint()

if __name__ == '__main__':
    asyncio.get_event_loop().run_until_complete(main())
