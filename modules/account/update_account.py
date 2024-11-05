import asyncio
from sys import stderr

from loguru import logger
from starknet_py.cairo.felt import decode_shortstring

from constants.data import *
from database.main import current_wallet, update_comment
from modules.utils import get_account, get_contract

logger.remove()
custom_name = "Upgrade Account"
logger.add(stderr, format="<white>{time:HH:mm:ss}</white> | <level>{level: <8}</level> | "
                          "<cyan>{extra[action]:<15}</cyan> | <white>{message}</white>")
logger = logger.bind(action=custom_name)


async def one_account_upgrade(wallet: dict,  index: int = 0):
    try:
        while True:
            try:

                account, session = await get_account(wallet=wallet)
                account_contract = await get_contract(account=account, address=int(wallet['public_key'], 16), abi=argentx_abi)

                version = (
                    await account_contract.functions['getVersion'].call()
                ).version

                version = decode_shortstring(version)
                break

            except Exception as ex:
                ex = str(ex).replace("\n", " - ")
                await session.close()
                logger.error(f'ERROR_1  | index = {index} | {wallet["public_key"]} | {ex}')

        logger.info(f'START    | index = {index} | {wallet["public_key"]}')

        if version == LAST_VERSION:
            logger.debug(f'UPDATED  | index = {index} | {wallet["public_key"]}')
            await session.close()
            return

        upgrade_call = account_contract.functions['upgrade'].prepare(
            implementation=IMPLEMENTATION_ADDRESS,
            calldata=[
                0
            ]
        )

        response = await account.execute(
            [
                upgrade_call
            ],
            auto_estimate=True
        )

        transaction = await account.client.wait_for_tx(response.transaction_hash)
        tx_hash = hex(response.transaction_hash)

        logger.success(f'FINISH   | index = {index} | {wallet["public_key"]} | Transaction: {STARKNET["voyager"]}/tx/{tx_hash}')
        await update_comment(public_key=wallet['public_key'], comment="updated")
        await session.close()

    except Exception as ex:
        await session.close()
        error = str(ex).replace("\n", " - ")
        logger.error(f'ERROR_3  | index = {index} | {wallet["public_key"]} | {error}')


async def main():
    wallet = {
        "public_key": "",
    }
    wallet = await current_wallet(public_key=wallet['public_key'])
    await one_account_upgrade(wallet=wallet)

if __name__ == '__main__':
    asyncio.get_event_loop().run_until_complete(main())

