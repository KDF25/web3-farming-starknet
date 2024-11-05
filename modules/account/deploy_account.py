import asyncio
import random
from sys import stderr

import aiohttp
from aiohttp_socks import ProxyConnector
from loguru import logger
from starknet_py.hash.address import compute_address
from starknet_py.hash.selector import get_selector_from_name
from starknet_py.net.account.account import Account
from starknet_py.net.gateway_client import GatewayClient
from starknet_py.net.models import StarknetChainId
from starknet_py.net.signer.stark_curve_signer import KeyPair

from config import all_proxies
from database.main import update_comment

logger.remove()
custom_name = "Deploy Account"
logger.add(stderr, format="<white>{time:HH:mm:ss}</white> | <level>{level: <8}</level> | "
                          "<cyan>{extra[action]:<15}</cyan> | <white>{message}</white>")
logger = logger.bind(action=custom_name)


async def one_account_deploy(wallet: dict, index: int =0):
    logger.info(f'START    | index = {index} | {wallet["public_key"]}')

    proxy_class_hash = 0x025ec026985a3bf9d0cc1fe17326b245dfdc3ff89b8fde106542a3ea56c5a918
    implementation_class_hash = 0x33434ad846cdd5f23eb73ff09fe6fddd568284a0fb7d1be20ee482f044dabe2

    selector = get_selector_from_name("initialize")
    private_key = wallet['private_key']
    private_key_int = int(private_key, 16)
    key_pair = KeyPair.from_private_key(private_key_int)
    calldata = [key_pair.public_key, 0]

    address = compute_address(class_hash=proxy_class_hash,
                              constructor_calldata=[implementation_class_hash, selector, len(calldata), *calldata],
                              salt=key_pair.public_key)

    proxy = random.choice(all_proxies)
    connector = ProxyConnector.from_url(proxy)
    session = aiohttp.ClientSession(connector=connector)

    client = GatewayClient(net="mainnet", session=session)
    chain = StarknetChainId.MAINNET
    constructor_calldata = [implementation_class_hash, selector, len(calldata), *calldata]

    account_deployment_result = await Account.deploy_account(
        address=address,
        class_hash=proxy_class_hash,
        salt=key_pair.public_key,
        key_pair=key_pair,
        client=client,
        chain=chain,
        constructor_calldata=constructor_calldata,
        max_fee=int(1e15),
    )

    await account_deployment_result.wait_for_acceptance()
    await update_comment(public_key=wallet['public_key'], comment="deployed")
    logger.success(f'FINISH   | index = {index} | {wallet["public_key"]}')
    await session.close()


if __name__ == '__main__':
    wallet = {
        "public_key": "",
        "private_key": ''
    }
    asyncio.get_event_loop().run_until_complete(one_account_deploy(wallet=wallet))
