import asyncio
from sys import stderr

from loguru import logger
from starknet_py.contract import Contract
from starknet_py.net.account.account import Account
from starknet_py.net.gateway_client import GatewayClient
from starknet_py.net.models import StarknetChainId
from starknet_py.net.signer.stark_curve_signer import KeyPair

from constants.data import STARKNET
from database.main import update_send_message
from modules.utils import *

import nltk
import random
from nltk.corpus import words

logger.remove()
custom_name = "Dmail"
logger.add(stderr, format="<white>{time:HH:mm:ss}</white> | <level>{level: <8}</level> | "
                          "<cyan>{extra[action]:<15}</cyan> | <white>{message}</white>")
logger = logger.bind(action=custom_name)

nltk.download('words')
english_words = words.words()


class Dmail:
    def __init__(self, wallet: dict,  index: int = 0, minuts: [float, int] = 0) -> None:
        self.__wallet = wallet
        self.__account = None
        self.__message = wallet.get('current_message')
        self.__mail = wallet.get('current_mail')
        self.__index = index
        self.__minuts = minuts

    async def _generate_message(self):
        breakers = ["", "!", ".", "?"]
        num_words = random.randint(1, 3)
        message = ' '.join(random.sample(english_words, num_words)) + random.choice(breakers)
        self.__message = message[0:30]

    async def _generate_mail(self):
        domain_list = ["@gmail.com", "@dmail.ai"]
        breakers = ["", "_", "."]
        num_words = random.randint(1, 2)
        mail = f'{random.choice(breakers)}'.join(random.sample(english_words, num_words))
        self.__mail = mail[0:20] + random.choice(domain_list)

    async def _random_parameters(self):
        await self._generate_message()
        await self._generate_mail()

    async def mail(self):
        await self._random_parameters()
        try:
            self.__account, session = await get_account(wallet=self.__wallet)
            dmail_router_address = int(STARKNET["dmail_router"], 16)

            while True:
                try:
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
                    logger.error(f'ERROR_1  | index = {self.__index} | {self.__wallet["public_key"]} | {ex}')

            logger.info(f'START    | index = {self.__index} | {self.__wallet["public_key"]} | Balance = {balance / 10 ** 18} ETH | {self.__mail} | {self.__message}')

            dmail_contract = await Contract.from_address(
                address=dmail_router_address,
                provider=self.__account,
                # proxy_config=True
            )

            dmail_call = dmail_contract.functions["transaction"].prepare(to=self.__mail, theme=self.__message)
            calls = dmail_call

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

            logger.success(f'FINISH   | index = {self.__index} | {self.__wallet["public_key"]} | Transaction: {STARKNET["voyager"]}/tx/{tx_hash} | SLEEP = {round(self.__minuts, 2)} min')
            await update_send_message(public_key=self.__wallet["public_key"], message=self.__message, mail=self.__mail)
            await session.close()
            await asyncio.sleep(self.__minuts * 60)

        except Exception as ex:
            ex = str(ex).replace("\n", " - ")
            await session.close()
            logger.error(f'ERROR_3  | index = {self.__index} | {self.__wallet["public_key"]} | {ex}')


async def main():
    wallet = {
        "public_key": "",
        "private_key": ''
    }
    start = Dmail(wallet=wallet)
    await start.mail()

if __name__ == '__main__':
    asyncio.get_event_loop().run_until_complete(main())
