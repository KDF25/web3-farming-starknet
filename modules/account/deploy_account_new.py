import asyncio
import random
from sys import stderr

import aiohttp
from aiohttp_socks import ProxyConnector
from loguru import logger
from starknet_py.net.account.account import Account
from starknet_py.net.gateway_client import GatewayClient
from starknet_py.net.models import StarknetChainId
from starknet_py.net.signer.stark_curve_signer import KeyPair

from config import all_proxies
from constants.data import STARKNET, IMPLEMENTATION_ADDRESS
from database.main import update_comment, current_wallet

logger.remove()
custom_name = "Deploy Account"
logger.add(stderr, format="<white>{time:HH:mm:ss}</white> | <level>{level: <8}</level> | "
                          "<cyan>{extra[action]:<15}</cyan> | <white>{message}</white>")
logger = logger.bind(action=custom_name)


async def one_account_deploy_new(wallet: dict, index: int =0):
    logger.info(f'START    | index = {index} | {wallet["public_key"]}')

    private_key = wallet['private_key']
    private_key_int = int(private_key, 16)
    key_pair = KeyPair.from_private_key(private_key_int)
    constructor_calldata = [key_pair.public_key, 0]

    proxy = random.choice(all_proxies)
    connector = ProxyConnector.from_url(proxy)
    session = aiohttp.ClientSession(connector=connector)

    client = GatewayClient(net="mainnet", session=session)
    chain = StarknetChainId.MAINNET

    account_deployment_result = await Account.deploy_account(
        address=int(wallet['public_key'], 16),
        class_hash=IMPLEMENTATION_ADDRESS,
        salt=key_pair.public_key,
        key_pair=key_pair,
        client=client,
        chain=chain,
        constructor_calldata=constructor_calldata,
        auto_estimate=True
    )

    await account_deployment_result.wait_for_acceptance()
    await update_comment(public_key=wallet['public_key'], comment="deployed")
    logger.success(f'FINISH   | index = {index} | {wallet["public_key"]} | Transaction: {STARKNET["voyager"]}/tx/{hex(account_deployment_result.hash)}')
    await session.close()


async def main():
    wallet = {
        "public_key": "",
    }
    wallet = await current_wallet(public_key=wallet['public_key'])
    await one_account_deploy_new(wallet=wallet)


if __name__ == '__main__':
    asyncio.get_event_loop().run_until_complete(main())
