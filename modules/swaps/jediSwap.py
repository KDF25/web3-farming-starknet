import asyncio
import time
from sys import stderr

from loguru import logger
from starknet_py.contract import Contract
from starknet_py.net.account.account import Account

from config import max_tries
from constants.data import STARKNET
from database.main import update_swap, current_wallet
from modules.utils import approve_token, get_account, get_from_token_contract, deposit_balance

logger.remove()
custom_name = "JediSwap"
logger.add(stderr, format="<white>{time:HH:mm:ss}</white> | <level>{level: <8}</level> | "
                          "<cyan>{extra[action]:<15}</cyan> | <white>{message}</white>")
logger = logger.bind(action=custom_name)


class JediSwap:
    def __init__(self, wallet: dict, from_token: str, to_token: str, amount: [float, int],
                 index: int = 0, minuts: [float, int] = 0) -> None:
        self.__account = None
        self.__wallet = wallet
        self.__from_token = from_token
        self.__to_token = to_token
        self.__amount = amount
        self.__index = index
        self.__minuts = minuts
        self.__repeat = 0

    async def swap(self):
        try:
            while True:
                try:
                    self.__account, session = await get_account(wallet=self.__wallet)
                    jediSwap_router_address = int(STARKNET["jediSwap_router"], 16)
                    from_token_address = int(STARKNET[self.__from_token], 16)
                    to_token_address = int(STARKNET[self.__to_token], 16)

                    eth_contract = await get_from_token_contract(account=self.__account, from_token="ETH",
                                                                 address=int(STARKNET["ETH"], 16))

                    balance = await eth_contract.functions['balanceOf'].prepare(
                        account=self.__account.address
                    ).call()

                    balance = balance[0]

                    from_token_contract = await get_from_token_contract(account=self.__account,
                                                                        from_token=self.__from_token,
                                                                        address=from_token_address)

                    token_decimals = await from_token_contract.functions['decimals'].call()
                    token_balance = await from_token_contract.functions['balanceOf'].prepare(
                        account=self.__account.address
                    ).call()

                    token_balance = token_balance[0]
                    token_decimals = token_decimals[0]
                    break

                except Exception as ex:
                    ex = str(ex).replace("\n", " - ")
                    await session.close()
                    logger.error(f'ERROR_1  | index = {self.__index} | {self.__wallet["public_key"]} | {self.__from_token} --> {self.__to_token} | {ex}')

            logger.info(f'START    | index = {self.__index} | {self.__wallet["public_key"]} | {self.__from_token} --> {self.__to_token} | {self.__from_token} = {token_balance / 10 ** token_decimals} | Balance = {balance / 10 ** 18} ETH ')

            if token_balance == 0:
                logger.debug(f'ZERO     | index = {self.__index} | {self.__wallet["public_key"]} | {self.__from_token} --> {self.__to_token} | {self.__from_token} = {token_balance / 10 ** token_decimals} | Balance = {balance / 10 ** 18} ETH ')
                await update_swap(public_key=self.__wallet['public_key'], amount=0 / 10 ** token_decimals,
                                  balance=balance, from_token=self.__from_token, to_token=self.__to_token,
                                  Swap="JediSwap")
                return

            amountIn = int(self.__amount * 10 ** token_decimals) if self.__from_token != "ETH" else await deposit_balance(balance=balance)

            if amountIn > token_balance:
                amountIn = token_balance

            calls = await approve_token(from_token_contract=from_token_contract, amount=amountIn,
                                        spender=jediSwap_router_address, owner=self.__account.address,
                                        from_token=self.__from_token, to_token=self.__to_token, index=self.__index)

            jediSwap_contract = await Contract.from_address(
                address=jediSwap_router_address,
                provider=self.__account,
                proxy_config=True
            )

            result = await jediSwap_contract.functions["get_amounts_out"].call(amountIn=amountIn,
                                                                               path=[
                                                                                   from_token_address,
                                                                                   to_token_address
                                                                               ])

            amountOut = result.amounts[1]
            deadline = int(time.time()) + 1200

            swap_call = jediSwap_contract.functions["swap_exact_tokens_for_tokens"].prepare(amountIn,
                                                                                            amountOut,
                                                                                            [from_token_address,
                                                                                             to_token_address],
                                                                                            self.__account.address,
                                                                                            deadline)

            calls.append(swap_call)

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
                    logger.error(f'ERROR_2  | index = {self.__index} | {self.__wallet["public_key"]} | {self.__from_token} --> {self.__to_token} | {ex}')

            logger.success(f'FINISH   | index = {self.__index} | {self.__wallet["public_key"]} | {self.__from_token} --> {self.__to_token} | Transaction: {STARKNET["voyager"]}/tx/{tx_hash} | Balance = {balance / 10 ** 18} ETH | SLEEP = {round(self.__minuts, 2)} min')
            await update_swap(public_key=self.__wallet['public_key'], amount=amountIn / 10 ** token_decimals,
                              balance=balance, from_token=self.__from_token, to_token=self.__to_token, Swap="JediSwap")
            await session.close()
            await asyncio.sleep(self.__minuts * 60)

        except Exception as ex:
            await session.close()
            error = str(ex).replace("\n", " - ")
            logger.error(f'ERROR_3  | index = {self.__index} | {self.__wallet["public_key"]} | {self.__from_token} --> {self.__to_token} | {error}')

            if self.__repeat < max_tries:
                await asyncio.sleep(5 * 60)
                self.__repeat += 1
                await self.swap()


async def main():
    wallet = {
        "public_key": "",
    }
    wallet = await current_wallet(public_key=wallet['public_key'])
    start = JediSwap(wallet=wallet, from_token="LORDS", to_token="ETH", amount=1000)
    await start.swap()

if __name__ == '__main__':
    asyncio.get_event_loop().run_until_complete(main())
