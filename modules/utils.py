import random
from sys import stderr

import aiohttp
from aiohttp_socks import ProxyConnector
from loguru import logger
from starknet_py.contract import Contract
from starknet_py.net.account.account import Account
from starknet_py.net.full_node_client import FullNodeClient
from starknet_py.net.gateway_client import GatewayClient
from starknet_py.net.models import StarknetChainId
from starknet_py.net.signer.stark_curve_signer import KeyPair

from config import all_proxies, ETH_PRICE
from constants.data import erc_20, STARKNET

logger.remove()
custom_name = "Utils"
logger.add(stderr, format="<white>{time:HH:mm:ss}</white> | <level>{level: <8}</level> | "
                          "<cyan>{extra[action]:<15}</cyan> | <white>{message}</white>")
logger = logger.bind(action=custom_name)


async def approve_token(from_token_contract: Contract, amount: [float, int], spender: int, owner: int, index: int,
                        from_token: str, to_token: str):
    allowance = await from_token_contract.functions['allowance'].prepare(
        spender=spender,
        owner=owner
    ).call()

    allowance = allowance[0]

    if allowance < amount:
        approve_call = from_token_contract.functions["approve"].prepare(
            spender=spender,
            amount=amount,
            max_fee=None

        )
        logger.info(f'APPROVED | index = {index} | 0x{hex(owner)[2:]} | {from_token} --> {to_token}')
        return [approve_call]

    return []


async def get_account(wallet: dict):
        private_key_int = int(wallet['private_key'], 16)
        public_key_int = int(wallet['public_key'], 16)
        key_pair = KeyPair(private_key=private_key_int, public_key=public_key_int)
        proxy = random.choice(all_proxies)
        connector = ProxyConnector.from_url(proxy)
        session = aiohttp.ClientSession(connector=connector)

        rpc = "https://starknet-mainnet.public.blastapi.io"
        client = FullNodeClient(node_url=rpc, session=session)

        account = Account(
            address=public_key_int,
            client=client,
            key_pair=key_pair,
            chain=StarknetChainId.MAINNET
        )
        account.ESTIMATED_FEE_MULTIPLIER = 2
        return account, session


async def get_from_token_contract(account: Account, from_token: str, address: int):
    if from_token.lower() == "ETH":
        return await Contract.from_address(
            address=address,
            provider=account,
            proxy_config=True
        )

    else:
        return Contract(
            address=address,
            abi=erc_20,
            provider=account
        )


async def get_contract(account: Account, address: int, abi: list):
    return Contract(
        address=address,
        abi=abi,
        provider=account
    )

async def deposit_balance(balance: int):
    usd_remainder = 4  # gas price for 2 transction
    current_eth_prise = ETH_PRICE  # current eth price
    amount = int(round(random.uniform(1, 1.5) * 0.015, 4) * 10 ** 18)

    if amount + (usd_remainder/current_eth_prise) * 10 ** 18 > balance:
        amount = balance - (usd_remainder / current_eth_prise) * 10 ** 18

    return int(amount)


async def zklend_deposit_balance(balance: int):
    usd_remainder = 5  # gas price for 2 transction
    current_eth_prise = ETH_PRICE  # current eth price
    amount = balance - (usd_remainder/current_eth_prise) * 10 ** 18
    # amount = (usd_remainder/current_eth_prise) * 10 ** 18
    return int(amount)


async def okx_deposit_balance(balance: int):
    usd_remainder = random.uniform(19, 21)
    current_eth_prise = ETH_PRICE  # current eth price
    amount = balance - (usd_remainder/current_eth_prise) * 10 ** 18
    return int(amount)


async def okx_deposit_balance2(balance: int, ETH: float):
    usd_remainder = random.uniform(0.5, 0.5)
    min_eth = usd_remainder / ETH_PRICE

    # if min_eth > ETH:
    amount = balance - min_eth * 10 ** 18
    # else:
    #     amount = balance - int(ETH * 10 ** 18 * random.uniform(0.9, 1.1))

    return int(amount)


async def check_token_balance(wallet: dict, token: str):
    while True:
        try:

            account, session = await get_account(wallet=wallet)
            token_address = int(STARKNET[token], 16)
            from_token_contract = await get_from_token_contract(account=account,  from_token=token, address=token_address)

            token_decimals = await from_token_contract.functions['decimals'].call()
            token_balance = await from_token_contract.functions['balanceOf'].prepare(
                account=account.address
            ).call()

            token_balance = token_balance[0]
            token_decimals = token_decimals[0]
            await session.close()
            return token_balance, token_decimals

        except Exception:
            await session.close()
            continue


def all_dex(modules: dict):
    ALL_DEX = {}
    if modules["JediSwap"]:
        ALL_DEX.update({"JediSwap": 1})
    if modules["10kSwap"]:
        ALL_DEX.update({"10kSwap": 2})
    if modules["MySwap"]:
        ALL_DEX.update({"MySwap": 3})
    if modules["AnvuSwap"]:
        ALL_DEX.update({"AnvuSwap": 4})
    if modules["sithswap"]:
        ALL_DEX.update({"sithswap": 5})
    if modules["starkexswap"]:
        ALL_DEX.update({"starkexswap": 6})
    if modules["fibrousswap"]:
        ALL_DEX.update({"fibrousswap": 7})
    return ALL_DEX



