import asyncio
from sys import stderr

from loguru import logger
from starknet_py.net.account.account import Account

from config import max_tries
from constants.data import STARKNET
from database.main import update_okx_deposit, current_wallet
from modules.utils import get_account, get_from_token_contract, okx_deposit_balance, okx_deposit_balance2

logger.remove()
custom_name = "Okx Deposit"
logger.add(stderr, format="<white>{time:HH:mm:ss}</white> | <level>{level: <8}</level> | "
                          "<cyan>{extra[action]:<15}</cyan> | <white>{message}</white>")
logger = logger.bind(action=custom_name)

slippage = 1


class OkxDeposit:
    def __init__(self, wallet: dict, amountIn: [float, int] = None, index: int = 0, minuts : [float, int] = 0) -> None:
        self.__repeat = 0
        self.__account = None
        self.__wallet = wallet
        self.__index = index
        self.__minuts = minuts
        self.__amountIn = amountIn
        self.__ETH = wallet['ETH']
        self.__recipient = int(self.__wallet['okx_address'], 16)

    async def transfer(self):
        try:
            while True:
                try:
                    self.__account, session = await get_account(wallet=self.__wallet)

                    eth_contract = await get_from_token_contract(account=self.__account, from_token="ETH",
                                                                 address=int(STARKNET["ETH"], 16))

                    balance = await eth_contract.functions['balanceOf'].prepare(
                        account=self.__account.address
                    ).call()
                    balance = balance[0]
                    break

                except Exception as ex:
                    ex = str(ex).replace("\n", " - ")
                    await session.close()
                    logger.error(f'ERROR_1  | index = {self.__index} | {self.__wallet["public_key"]} | {self.__wallet["okx_address"]} | {ex}')

            logger.info(f'START    | index = {self.__index} | {self.__wallet["public_key"]} | {self.__wallet["okx_address"]} | Balance = {balance / 10 ** 18} ETH ')

            # amountIn = await okx_deposit_balance(balance=balance) if self.__amountIn is None else int(self.__amountIn * 10 ** 18)
            amountIn = await okx_deposit_balance2(balance=balance, ETH=self.__ETH)

            transfer_call = eth_contract.functions["transfer"].prepare(
                recipient=self.__recipient,
                amount=amountIn,
            )

            calls = [transfer_call]

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

            while True:
                try:
                    balance = await eth_contract.functions['balanceOf'].prepare(
                        account=self.__account.address
                    ).call()

                    balance = balance[0]
                    break

                except Exception as ex:
                    ex = str(ex).replace("\n", " - ")
                    logger.error(f'ERROR_2  | index = {self.__index} | {self.__wallet["public_key"]} | {ex}')

            logger.success(f'FINISH   | index = {self.__index} | {self.__wallet["public_key"]} | Transaction: {STARKNET["voyager"]}/tx/{tx_hash} | Transfer = {amountIn / 10 ** 18} ETH | SLEEP = {round(self.__minuts, 2)} min')
            await update_okx_deposit(public_key=self.__wallet['public_key'], balance=balance)
            await session.close()
            await asyncio.sleep(self.__minuts * 60)

        except Exception as ex:
            ex = str(ex).replace("\n", " - ")
            await session.close()
            logger.error(f'ERROR_3  | index = {self.__index} | {self.__wallet["public_key"]} | {ex}')

            if self.__repeat < max_tries:
                await asyncio.sleep(5 * 60)
                self.__repeat += 1
                await self.transfer()


async def main():
    wallet = {
        "public_key": "",
    }
    wallet = await current_wallet(public_key=wallet['public_key'])
    start = OkxDeposit(wallet=wallet)
    await start.transfer()


if __name__ == '__main__':
    asyncio.get_event_loop().run_until_complete(main())
