import asyncio
import random

from config import max_tries

from modules.utils import *

logger.remove()
custom_name = "QuantumLeapNft"
logger.add(stderr, format="<white>{time:HH:mm:ss}</white> | <level>{level: <8}</level> | "
                          "<cyan>{extra[action]:<15}</cyan> | <white>{message}</white>")
logger = logger.bind(action=custom_name)


class QuantumLeapNft:
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
                    mint_router_address = int(STARKNET["quantumleapnft_router"], 16)
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
                    logger.error(f'ERROR_1 |  index = {self.__index} | {self.__wallet["public_key"]} | {ex}')

            logger.info(f'START    |  index = {self.__index} | {self.__wallet["public_key"]} | Balance = {balance / 10 ** 18} ETH ')

            mint_contract = await Contract.from_address(
                address=mint_router_address,
                provider=self.__account,
                proxy_config=True
            )

            mint_call = mint_contract.functions["mintPublic"].prepare(to=self.__account.address)

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
            # await update_mint_nft(public_key=self.__wallet["public_key"], nft_id=0)
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




async def main(wallet: dict, index: int):
    logger.info(f"SWAPS | index = {index} | {wallet['public_key']}")
    await asyncio.sleep(int(0 + index * random.randint(5,7) * 60))
    start = QuantumLeapNft(wallet=wallet, index=index)
    await start.mint()

async def cycle():

    wallets = [
        {
            "public_key": "",
            "private_key": '',
        },
    ]
    tasks = []
    for index, wallet in enumerate(wallets):

        await main(wallet=wallet, index=index)
        await asyncio.sleep(random.uniform(5, 15) * 60)

        task = asyncio.create_task(main(wallet=wallet, index=index))
        tasks.append(task)

    while len(tasks) > 0:
        tasks[:] = [task for task in tasks if not task.done()]
        await asyncio.sleep(60)


if __name__ == '__main__':
    asyncio.get_event_loop().run_until_complete(cycle())
