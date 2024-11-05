import asyncio
import random
from sys import stderr

from loguru import logger
from starknet_py.contract import Contract
from starknet_py.net.account.account import Account

from config import max_tries
from constants.data import STARKNET, zklend_abi
from database.main import update_zklend, current_wallet
from modules.utils import get_account, get_from_token_contract

logger.remove()
custom_name = "ZkLend Borrow"
logger.add(stderr, format="<white>{time:HH:mm:ss}</white> | <level>{level: <8}</level> | "
                          "<cyan>{extra[action]:<15}</cyan> | <white>{message}</white>")
logger = logger.bind(action=custom_name)


class ZkLendBorrow:
    def __init__(self, wallet: dict, from_token: str, to_token: str,  index: int = 0, minuts: [float, int] = 0) -> None:
        self.__repeat = 0
        self.__account = None
        self.__wallet = wallet
        self.__from_token = from_token
        self.__to_token = to_token
        self.__from_token_address = int(STARKNET[self.__from_token], 16)
        self.__to_token_address = int(STARKNET[self.__to_token], 16)
        self.__index = index
        self.__minuts = minuts

    async def _get_amount(self):
        deposit = self.__wallet['zklend'].get("deposit")
        self.__amountIn = int(deposit * random.uniform(0.6, 0.75))
        self.__amountOut = self.__amountIn
        if self.__from_token != self.__to_token:
            jediSwap_router_address = int(STARKNET["jediSwap_router"], 16)
            jediSwap_contract = await Contract.from_address(
                address=jediSwap_router_address,
                provider=self.__account,
                proxy_config=True
            )
            result = await jediSwap_contract.functions["get_amounts_out"].call(amountIn=self.__amountIn,
                                                                               path=[
                                                                                   self.__from_token_address,
                                                                                   self.__to_token_address
                                                                               ])

            self.__amountOut = result.amounts[1]

    async def start(self):
        try:
            while True:
                try:
                    self.__account, session = await get_account(wallet=self.__wallet)
                    zklend_router_address = int(STARKNET["zklend_router"], 16)

                    eth_contract = await get_from_token_contract(account=self.__account, from_token="ETH",
                                                                 address=int(STARKNET["ETH"], 16))

                    balance = await eth_contract.functions['balanceOf'].prepare(
                        account=self.__account.address
                    ).call()

                    balance = balance[0]

                    token_contract = await get_from_token_contract(account=self.__account,
                                                                   from_token=self.__to_token,
                                                                   address=self.__to_token_address)

                    token_decimals = await token_contract.functions['decimals'].call()
                    token_decimals = token_decimals[0]
                    break

                except Exception as ex:
                    ex = str(ex).replace("\n", " - ")
                    await session.close()
                    logger.error(f'ERROR_1  | index = {self.__index} | {self.__wallet["public_key"]} | {self.__from_token} | {ex}')

            logger.info(f'START    | index = {self.__index} | {self.__wallet["public_key"]} | {self.__from_token} | Balance = {balance / 10 ** 18} ETH ')

            await self._get_amount()

            zklend_contract = Contract(
                address=zklend_router_address,
                provider=self.__account,
                abi=zklend_abi,
            )

            borrow_call = zklend_contract.functions["borrow"].prepare(
                token=self.__to_token_address,
                amount=self.__amountOut
            )

            calls = [borrow_call]

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

            logger.success(f'FINISH   | index = {self.__index} | {self.__wallet["public_key"]} | {self.__from_token} | Transaction: {STARKNET["voyager"]}/tx/{tx_hash} | Balance = {balance / 10 ** 18} ETH | SLEEP = {round(self.__minuts, 2)} min')

            route: list = self.__wallet['zklend'].get("route", [])
            route.append(f"{custom_name}|{self.__to_token}|{round(self.__amountOut/ 10 ** token_decimals, 6)}")
            self.__wallet['zklend']["borrow_count"] = self.__wallet['zklend'].get("borrow_count", 0) + 1
            self.__wallet['zklend']["total_volume"] = self.__wallet['zklend'].get("total_volume", 0) + self.__amountIn
            self.__wallet['zklend'].update({"borrow": self.__amountOut, "borrow_token": self.__to_token, "route": route})
            await update_zklend(public_key=self.__wallet['public_key'], zklend=self.__wallet['zklend'])

            await session.close()
            await asyncio.sleep(self.__minuts * 60)

        except Exception as ex:
            await session.close()
            error = str(ex).replace("\n", " - ")
            logger.error(f'ERROR_3  | index = {self.__index} | {self.__wallet["public_key"]} | {self.__from_token} | {error}')

            if self.__repeat < max_tries:
                await asyncio.sleep(5 * 60)
                self.__repeat += 1
                await self.start()
        #

async def main():

    wallet = {
        "public_key": "",
        "private_key": ''
    }
    wallet = await current_wallet(public_key=wallet['public_key'])
    start = ZkLendBorrow(wallet=wallet, from_token="ETH", to_token="USDC")
    await start.start()



if __name__ == '__main__':
    asyncio.get_event_loop().run_until_complete(main())
