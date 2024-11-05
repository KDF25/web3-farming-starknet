import asyncio
from sys import stderr

from loguru import logger
from starknet_py.contract import Contract
from starknet_py.net.account.account import Account

from config import max_tries
from constants.data import STARKNET, zklend_abi
from database.main import update_zklend, current_wallet
from modules.utils import get_account, get_from_token_contract, zklend_deposit_balance

logger.remove()
custom_name = "ZkLend Deposit"
logger.add(stderr, format="<white>{time:HH:mm:ss}</white> | <level>{level: <8}</level> | "
                          "<cyan>{extra[action]:<15}</cyan> | <white>{message}</white>")
logger = logger.bind(action=custom_name)


class ZkLendDeposit:
    def __init__(self, wallet: dict, from_token: str, index: int = 0, minuts: [float, int] = 0) -> None:
        self.__repeat = 0
        self.__account = None
        self.__wallet = wallet
        self.__from_token = from_token
        self.__index = index
        self.__minuts = minuts

    async def start(self):
        try:
            while True:
                try:
                    self.__account, session = await get_account(wallet=self.__wallet)
                    zklend_router_address = int(STARKNET["zklend_router"], 16)
                    from_token_address = int(STARKNET[self.__from_token], 16)

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
                    logger.error(f'ERROR_1  | index = {self.__index} | {self.__wallet["public_key"]} | {self.__from_token} | {ex}')

            logger.info(f'START    | index = {self.__index} | {self.__wallet["public_key"]} | {self.__from_token} | {self.__from_token} = {token_balance / 10 ** token_decimals} | Balance = {balance / 10 ** 18} ETH ')

            amountIn = await zklend_deposit_balance(balance=balance)

            zklend_contract = Contract(
                address=zklend_router_address,
                provider=self.__account,
                abi=zklend_abi,
            )

            approve_call = from_token_contract.functions["approve"].prepare(
                spender=zklend_router_address,
                amount=amountIn,
                max_fee=None
            )

            deposit_call = zklend_contract.functions["deposit"].prepare(
                token=from_token_address,
                amount=amountIn
            )

            enable_collateral_call = zklend_contract.functions["enable_collateral"].prepare(
                token=from_token_address
            )

            calls = [approve_call, deposit_call, enable_collateral_call]

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
            route.append(f"{custom_name}|{self.__from_token}|{round(amountIn/ 10 ** token_decimals, 6)}")
            self.__wallet['zklend']["deposit_count"] = self.__wallet['zklend'].get("deposit_count", 0) + 1
            self.__wallet['zklend']["total_volume"] = self.__wallet['zklend'].get("total_volume", 0) + amountIn
            self.__wallet['zklend'].update({"deposit": amountIn, "deposit_token": self.__from_token, "route": route})
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


async def main():
    wallet = {
        "public_key": "",
    }
    wallet = await current_wallet(public_key= wallet['public_key'])
    start = ZkLendDeposit(wallet=wallet, from_token="ETH")
    await start.start()


if __name__ == '__main__':
    asyncio.get_event_loop().run_until_complete(main())
