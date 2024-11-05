import asyncio
import json
from typing import Literal

import psycopg2
from sqlalchemy import create_engine
import pandas as pd
from starknet_py.net.signer.stark_curve_signer import KeyPair

pg_host = ""
pg_user = ""
pg_password = ''

database = ""


async def main_database_create():
    pg_host_url = f'postgresql://{pg_user}:{pg_password}@{pg_host}:5432/{database}'
    engine = create_engine(pg_host_url)
    df = pd.read_excel('starknet_all.xlsx', sheet_name="Лист3")
    df.to_sql('wallets', engine, index=False, if_exists="replace")


async def mySwap_pools_database_create():
    pg_host_url = f'postgresql://{pg_user}:{pg_password}@{pg_host}:5432/{database}'
    engine = create_engine(pg_host_url)
    df = pd.read_excel('mySwapPools.xlsx')
    df.to_sql('mySwapPools', engine, index=False, if_exists="replace")


async def fibrousSwap_pools_database_create():
    pg_host_url = f'postgresql://{pg_user}:{pg_password}@{pg_host}:5432/{database}'
    engine = create_engine(pg_host_url)
    df = pd.read_excel('fibrousSwapPools.xlsx')
    df.to_sql('fibrousSwapPools', engine, index=False, if_exists="replace")


async def update_first_withdraw(public_key: str, currency: [float, int], Mainnet: Literal["ARBITRUM", "OPTIMISM"]):
    conn = psycopg2.connect(
        host=pg_host,
        user=pg_user,
        password=pg_password, database=database)
    conn.autocommit = True
    sql = f"""update public.wallets set "ETH" = {currency}, comment = '{Mainnet}'  WHERE public_key = '{public_key}'"""
    cursor = conn.cursor()
    cursor.execute(sql)
    cursor.close()
    conn.close()


async def update_swap(public_key: str, from_token: str,  to_token: str, balance: [float, int], amount: [float, int],
                      Swap: Literal["JediSwap", "10kSwap", "MySwap", "AnvuSwap", "sithswap", "starkexswap", "fibrousswap"]):
    conn = psycopg2.connect(
        host=pg_host,
        user=pg_user,
        password=pg_password, database=database)
    conn.autocommit = True
    balance /= 10 ** 18

    sql = f"""  update public.wallets 
                set "ETH" = '{balance}', 
                "Tokens" = CASE
                WHEN '{from_token}' = 'ETH' THEN ARRAY_APPEND("Tokens", '{to_token}')
                WHEN '{to_token}' = 'USDC' AND 'USDC' <> ALL ("Tokens") THEN ARRAY_APPEND(ARRAY_REMOVE("Tokens", '{from_token}'), '{to_token}')
                ELSE ARRAY_REMOVE("Tokens", '{from_token}')
                 END,
                route = ARRAY_APPEND(route, '{from_token}-->{to_token}|{Swap}|{amount}'), 
                "{Swap}" = "{Swap}" + 1,  
                all_swaps = all_swaps + 1  
                WHERE public_key = '{public_key}'"""

    cursor = conn.cursor()
    cursor.execute(sql)
    cursor.close()
    conn.close()


async def update_okx_deposit(public_key: str, balance: int):
    conn = psycopg2.connect(
        host=pg_host,
        user=pg_user,
        password=pg_password, database=database)
    conn.autocommit = True
    balance /= 10 ** 18
    sql = f"""update public.wallets set "comment" = 'okx_deposit', "ETH" = '{balance}'  WHERE public_key = '{public_key}'"""
    cursor = conn.cursor()
    cursor.execute(sql)
    cursor.close()
    conn.close()


async def remove_no_token(public_key: str, from_token: str):
    conn = psycopg2.connect(
        host=pg_host,
        user=pg_user,
        password=pg_password, database=database)
    conn.autocommit = True

    sql = f"""  update public.wallets 
                set  "Tokens" = ARRAY_REMOVE("Tokens", '{from_token}') 
                WHERE public_key = '{public_key}'"""

    cursor = conn.cursor()
    cursor.execute(sql)
    cursor.close()
    conn.close()


async def all_wallets(limit: int, offset: int = 0):
    conn = psycopg2.connect(
        host=pg_host,
        user=pg_user,
        password=pg_password, database=database)
    df = pd.read_sql(f"""SELECT * FROM public.wallets WHERE comment = 'BRIDGED' and id < 115 ORDER BY id LIMIT {limit} OFFSET {offset}""", con=conn)
    conn.close()
    df = df.reset_index(drop=True).to_dict('records')
    return df


async def all_wallets_to_bridge(limit: int, offset: int = 0):
    conn = psycopg2.connect(
        host=pg_host,
        user=pg_user,
        password=pg_password, database=database)
    df = pd.read_sql(f"""SELECT private_key, public_key, "Tokens", "comment"  FROM public.wallets  
                         WHERE comment != 'BRIDGED' and id <= 210
                         ORDER BY "ETH" LIMIT {limit} OFFSET {offset}""", con=conn)
    conn.close()
    df = df.reset_index(drop=True).to_dict('records')
    return df


async def all_wallets_to_swap(limit: int, offset: int = 0):
    conn = psycopg2.connect(
        host=pg_host,
        user=pg_user,
        password=pg_password, database=database)
    df = pd.read_sql(f"""SELECT * FROM public.wallets  
                         WHERE id >=40 and id <= 230  and "ETH" != 0
                         ORDER BY id ASC  LIMIT {limit} OFFSET {offset}""", con=conn)
    conn.close()
    df = df.reset_index(drop=True).to_dict('records')
    return df


async def all_wallets_to_lending(limit: int, offset: int = 0):
    conn = psycopg2.connect(
        host=pg_host,
        user=pg_user,
        password=pg_password, database=database)
    eth_max = int(0.75 * 10 ** 18)
    # eth_max = int(0 * 10 ** 18)
    # df = pd.read_sql(f"""select * from wallets WHERE id = 2
    #                      ORDER BY RANDOM()  LIMIT {limit} OFFSET {offset}""", con=conn)
    df = pd.read_sql(f"""select * from wallets WHERE (zklend->>'total_volume')::Bigint <= {eth_max} and id >= 16 and id <= 16 
                         ORDER BY RANDOM()  LIMIT {limit} OFFSET {offset}""", con=conn)
    conn.close()
    df = df.reset_index(drop=True).to_dict('records')
    return df


async def all_wallets_to_deploy(limit: int, offset: int = 0):
    conn = psycopg2.connect(
        host=pg_host,
        user=pg_user,
        password=pg_password, database=database)
    df = pd.read_sql(f"""SELECT * FROM public.wallets  
                         WHERE comment = 'BRIDGED' 
                         ORDER BY RANDOM()  LIMIT {limit} OFFSET {offset}""", con=conn)
    conn.close()
    df = df.reset_index(drop=True).to_dict('records')
    return df


async def all_wallets_to_upgrade(limit: int, offset: int = 0):
    conn = psycopg2.connect(
        host=pg_host,
        user=pg_user,
        password=pg_password, database=database)
    # df = pd.read_sql(f"""SELECT * FROM public.wallets
    #                      WHERE comment = 'deployed'
    #                      ORDER BY RANDOM()  LIMIT {limit} OFFSET {offset}""", con=conn)
    df = pd.read_sql(f"""SELECT * FROM public.wallets  
                             WHERE id >0 and id <=173 and comment = 'deployed' 
                             ORDER BY RANDOM()  LIMIT {limit} OFFSET {offset}""", con=conn)
    conn.close()
    df = df.reset_index(drop=True).to_dict('records')
    return df


async def all_wallets_to_transfer(limit: int, offset: int = 0):
    conn = psycopg2.connect(
        host=pg_host,
        user=pg_user,
        password=pg_password, database=database)
    # df = pd.read_sql(f"""SELECT * FROM public.wallets
    #                      WHERE id >89 and id <=93
    #                      ORDER BY RANDOM()  LIMIT {limit} OFFSET {offset}""", con=conn)
    df = pd.read_sql(f"""SELECT * FROM public.wallets
                         WHERE okx_address != '*' and id <= 173 and id >= 120
                         ORDER BY id ASC  LIMIT {limit} OFFSET {offset}""", con=conn)
    conn.close()
    df = df.reset_index(drop=True).to_dict('records')
    return df


async def current_wallet(public_key: str):
    conn = psycopg2.connect(
        host=pg_host,
        user=pg_user,
        password=pg_password, database=database)
    df = pd.read_sql(f"""SELECT * FROM public.wallets WHERE public_key = '{public_key}' """, con=conn)
    conn.close()
    df = df.reset_index(drop=True).to_dict('records')
    return df[0]


async def current_swaps(public_key: str):
    conn = psycopg2.connect(
        host=pg_host,
        user=pg_user,
        password=pg_password, database=database)
    df = pd.read_sql(f"""SELECT "JediSwap", "10kSwap", "MySwap", "AnvuSwap", "sithswap", "starkexswap", "fibrousswap"
                          FROM public.wallets WHERE public_key = '{public_key}' """, con=conn)
    conn.close()
    df = df.reset_index(drop=True).to_dict('records')
    return df[0]


async def current_pool_mySwap(from_token: str, to_token: str):
    conn = psycopg2.connect(
        host=pg_host,
        user=pg_user,
        password=pg_password, database=database)
    df = pd.read_sql(f"""SELECT pool_id FROM "mySwapPools" 
                         WHERE '{from_token}' = ANY("Tokens") and '{to_token}' = ANY("Tokens")""", con=conn)
    conn.close()
    df = df.reset_index(drop=True).to_dict('records')
    return df[0]


async def current_pool_fibrousSwap(from_token: str, to_token: str, swap: Literal["jediSwap", "tenKSwap", "mySwap"]):
    conn = psycopg2.connect(
        host=pg_host,
        user=pg_user,
        password=pg_password, database=database)
    df = pd.read_sql(f"""SELECT "{swap}" FROM "fibrousSwapPools" 
                         WHERE '{from_token}' = ANY("Tokens") and '{to_token}' = ANY("Tokens")""", con=conn)
    conn.close()
    df = df.reset_index(drop=True).to_dict('records')
    return df[0]


async def update_exchange_withdraw(public_key: str,  currency: [float, int]):
    conn = psycopg2.connect(
        host=pg_host,
        user=pg_user,
        password=pg_password, database=database)
    conn.autocommit = True
    sql = f"""update public.wallets set "ETH" = '{currency}', "comment" = 'withdraw'  WHERE public_key = '{public_key}'"""
    cursor = conn.cursor()
    cursor.execute(sql)
    cursor.close()
    conn.close()


async def update_comment(public_key: str, comment: str):
    conn = psycopg2.connect(
        host=pg_host,
        user=pg_user,
        password=pg_password, database=database)
    conn.autocommit = True
    sql = f"""update public.wallets set  "comment" = '{comment}'  WHERE public_key = '{public_key}'"""
    cursor = conn.cursor()
    cursor.execute(sql)
    cursor.close()
    conn.close()


async def update_zklend(public_key: str, zklend: dict):
    conn = psycopg2.connect(
        host=pg_host,
        user=pg_user,
        password=pg_password, database=database)
    conn.autocommit = True
    sql = """UPDATE public.wallets SET "zklend" = %s, "zklend_count" = "zklend_count" + 1 WHERE public_key = %s"""
    cursor = conn.cursor()
    zklend_json = json.dumps(zklend)
    cursor.execute(sql, (zklend_json, public_key))
    cursor.close()
    conn.close()


async def update_all_tokens(public_key: str, TOKENS: list, comment: str):
    conn = psycopg2.connect(
        host=pg_host,
        user=pg_user,
        password=pg_password, database=database)
    conn.autocommit = True
    tokens_json = json.dumps(TOKENS).replace("[", "{").replace("]", "}")
    sql = f"""update public.wallets set "Tokens" = '{tokens_json}', comment = '{comment}' WHERE public_key = '{public_key}'"""
    cursor = conn.cursor()
    cursor.execute(sql)
    cursor.close()
    conn.close()


async def all_wallets_to_check(limit: int, offset: int = 0):
    conn = psycopg2.connect(
        host=pg_host,
        user=pg_user,
        password=pg_password, database=database)
    df = pd.read_sql(f"""SELECT * FROM public.wallets WHERE id >=0 and id <=230 ORDER BY id LIMIT {limit} OFFSET {offset}""", con=conn)
    conn.close()
    df = df.reset_index(drop=True).to_dict('records')
    return df


async def update_mint_nft(public_key: str, nft_id: int):
    conn = psycopg2.connect(
        host=pg_host,
        user=pg_user,
        password=pg_password, database=database)
    conn.autocommit = True
    sql = f"""update public.wallets set
              nft_id = ARRAY_APPEND(nft_id, {nft_id}),  
              mint_count = mint_count + 1   
              WHERE public_key = '{public_key}'"""
    cursor = conn.cursor()
    cursor.execute(sql)
    cursor.close()
    conn.close()


async def update_send_message(public_key: str, message: str, mail: str):
    conn = psycopg2.connect(
        host=pg_host,
        user=pg_user,
        password=pg_password, database=database)
    conn.autocommit = True
    sql = f"""update public.wallets set 
              message_count = message_count + 1, 
              message_route = ARRAY_APPEND(message_route, '{message} | {mail}') 
              WHERE public_key = '{public_key}'"""
    cursor = conn.cursor()
    cursor.execute(sql)
    cursor.close()
    conn.close()


async def all_wallets_to_action(limit: int, offset: int = 0):
    conn = psycopg2.connect(
        host=pg_host,
        user=pg_user,
        password=pg_password, database=database)
    # df = pd.read_sql(f"""SELECT * FROM public.wallets
    #                      WHERE comment = 'deployed' and (mint_count = 0 or message_count = 0)
    #                      ORDER BY all_swaps LIMIT {limit} OFFSET {offset}""", con=conn)
    df = pd.read_sql(f"""SELECT * FROM public.wallets
                         WHERE id >= 0 and id <= 175 and "ETH" != 0 
                         ORDER BY RANDOM() LIMIT {limit} OFFSET {offset}""", con=conn)
    # df = pd.read_sql(f"""SELECT * FROM public.wallets
    #                      WHERE message_count <= 3 and "ETH" != 0
    #                      ORDER BY RANDOM() LIMIT {limit} OFFSET {offset}""", con=conn)
    # df = pd.read_sql(f"""SELECT * FROM public.wallets
    #                      WHERE id >=200 and id <=230
    #                      ORDER BY RANDOM() LIMIT {limit} OFFSET {offset}""", con=conn)
    conn.close()
    df = df.reset_index(drop=True).to_dict('records')
    return df


async def update_current_message(id: int, message: str):
    conn = psycopg2.connect(
        host=pg_host,
        user=pg_user,
        password=pg_password, database=database)
    conn.autocommit = True
    sql = f"""update public.wallets set current_message = '{message}'  WHERE id = {id}"""
    cursor = conn.cursor()
    cursor.execute(sql)
    cursor.close()
    conn.close()


async def update_current_mail(id: int, mail: str):
    conn = psycopg2.connect(
        host=pg_host,
        user=pg_user,
        password=pg_password, database=database)
    conn.autocommit = True
    sql = f"""update public.wallets set current_mail = '{mail}'  WHERE id = {id}"""
    cursor = conn.cursor()
    cursor.execute(sql)
    cursor.close()
    conn.close()


async def set_messages():
    message_list = [
        "david_apple @ gmail.com",
        "emily_mountain @ gmail.com",
        "grace_unicorn @ gmail.com",
        "isabel_penguin @ gmail.com",
        "jack_river @ gmail.com",
        "kate_lion @ gmail.com",
        "leo_tiger @ gmail.com",
        "molly_butterfly @ gmail.com",
        "noah_sunflower @ gmail.com",
        "olivia_dolphin @ gmail.com",
        "bob_sunflower @ gmail.com",
        "hank_thunder @ gmail.com",
        "carol_dolphin @ gmail.com",
        "peter_apple @ gmail.com",
        "tom_star @ gmail.com",
        "victor_river @ gmail.com",
        "xander_fire @ gmail.com",
        "yara_earth @ gmail.com",
        "zack_moon @ gmail.com",
        "anna_star @ gmail.com",
        "ben_sun @ gmail.com",
        "daniel_rain @ gmail.com",
        "emma_ocean @ gmail.com",
        "isabel_flower @ gmail.com",
        "hannah_sunset @ gmail.com",
        "riley_rainbow @ gmail.com",
        "isaac_river @ gmail.com",
        "jasmine_garden @ gmail.com",
        "sophia_unicorn @ gmail.com",
        "kevin_mountain @ gmail.com",
        "lily_sky @ gmail.com",
        "max_dolphin @ gmail.com",
        "oliver_rose @ gmail.com",
        "piper_tree @ gmail.com",
        "quincy_sunflower @ gmail.com",
        "sophie_bird @ gmail.com",
        "tyler_beach @ gmail.com",
        "grace_snow @ gmail.com",
        "jack_sun @ gmail.com",
        "william_lake @ gmail.com",
        "xena_forest @ gmail.com",
        "yasmin_rainbow @ gmail.com",
        "zachary_cloud @ gmail.com",
        "avery_thunder @ gmail.com",
        "bella_flower @ gmail.com",
        "caleb_mountain @ gmail.com",
        "daisy_river @ gmail.com",
        "elijah_snow @ gmail.com",
        "freya_star @ gmail.com",
        "george_dolphin @ gmail.com",
        "holly_butterfly @ gmail.com",
        "isabelle_rain @ gmail.com",
        "victor_sunset @ gmail.com",
        "kate_star @ gmail.com",
        "mia_sunflower @ gmail.com",
        "nathan_beach @ gmail.com",
        "parker_bird @ gmail.com",
        "quinn_star @ gmail.com",
        "riley_moon @ gmail.com",
        "sophia_wave @ gmail.com",
        "ursula_lion @ gmail.com",
        "victor_tiger @ gmail.com",
        "xavier_cloud @ gmail.com",
        "yvonne_moon @ gmail.com",
        "tristan_leaf @ gmail.com",
        "clara_ocean @ gmail.com",
        "daniel_snow @ gmail.com",
        "emma_star @ gmail.com",
        "finn_dolphin @ gmail.com",
        "grace_butterfly @ gmail.com",
        "isabel_wave @ gmail.com",
        "kylie_cloud @ gmail.com",
        "jack_river @ gmail.com",
        "kate_bird @ gmail.com",
        "leo_star @ gmail.com",
        "mia_sunflower @ gmail.com",
        "noah_lion @ gmail.com",
        "olivia_tiger @ gmail.com",
        "ava_sun @ gmail.com",
        "benjamin_mountain @ gmail.com",
        "sophia_star @ gmail.com",
        "tristan_sun @ gmail.com",
        "ursula_wave @ gmail.com",
        "victor_sunset @ gmail.com",
        "willow_dolphin @ gmail.com",
        "xavier_butterfly @ gmail.com",
        "yvonne_star @ gmail.com",
        "zane_moon @ gmail.com",
        "amelia_river @ gmail.com",
        "benjamin_fire @ gmail.com",
        "clara_moon @ gmail.com",
        "daniel_cloud @ gmail.com",
        "emma_bird @ gmail.com",
        "finn_star @ gmail.com",
        "grace_sunflower @ gmail.com",
        "hank_rainbow @ gmail.com",
        "isabel_unicorn @ gmail.com",
        "jack_star @ gmail.com",
        "kate_dolphin @ gmail.com",
        "leo_cloud @ gmail.com",
        "mia_wave @ gmail.com",
        "noah_star @ gmail.com",
        "olivia_sun @ gmail.com",
        "parker_moon @ gmail.com",
        "quinn_wave @ gmail.com",
        "riley_star @ gmail.com",
        "sophia_mountain @ gmail.com",
        "tristan_river @ gmail.com",
        "ursula_dolphin @ gmail.com",
        "victor_butterfly @ gmail.com",
        "willow_rainbow @ gmail.com",
        "xavier_unicorn @ gmail.com",
        "yvonne_star @ gmail.com",
        "zane_sunflower @ gmail.com",
        "amelia_moon @ gmail.com",
        "benjamin_bird @ gmail.com",
        "clara_star @ gmail.com",
        "daniel_sun @ gmail.com",
        "emma_ocean @ gmail.com",
        "finn_dolphin @ gmail.com",
        "grace_butterfly @ gmail.com",
        "hank_rainbow @ gmail.com",
        "isabel_unicorn @ gmail.com",
        "jack_star @ gmail.com",
        "kate_dolphin @ gmail.com",
        "leo_cloud @ gmail.com",
        "mia_wave @ gmail.com",
        "noah_star @ gmail.com",
        "olivia_sun @ gmail.com",
        "parker_moon @ gmail.com",
        "quinn_wave @ gmail.com",
        "riley_star @ gmail.com",
        "sophia_mountain @ gmail.com",
        "tristan_river @ gmail.com",
        "ursula_dolphin @ gmail.com",
        "victor_butterfly @ gmail.com",
        "willow_rainbow @ gmail.com",
        "xavier_unicorn @ gmail.com",
        "yvonne_star @ gmail.com",
        "zane_sunflower @ gmail.com",
        "amelia_moon @ gmail.com",
        "benjamin_bird @ gmail.com",
        "clara_star @ gmail.com",
        "daniel_sun @ gmail.com",
        "emma_ocean @ gmail.com",
        "finn_dolphin @ gmail.com",
        "grace_butterfly @ gmail.com",
        "hank_rainbow @ gmail.com",
        "isabel_unicorn @ gmail.com",
        "jack_star @ gmail.com",
        "kate_dolphin @ gmail.com",
        "leo_cloud @ gmail.com",
        "mia_wave @ gmail.com",
        "noah_star @ gmail.com",
        "olivia_sun @ gmail.com",
        "parker_moon @ gmail.com",
        "quinn_wave @ gmail.com",
        "riley_star @ gmail.com",
        "sophia_mountain @ gmail.com",
        "tristan_river @ gmail.com",
        "ursula_dolphin @ gmail.com",
        "victor_butterfly @ gmail.com",
        "willow_rainbow @ gmail.com",
        "xavier_unicorn @ gmail.com",
        "yvonne_star @ gmail.com",
        "zane_sunflower @ gmail.com",
        "amelia_moon @ gmail.com",
        "benjamin_bird @ gmail.com",
        "clara_star @ gmail.com",
        "daniel_sun @ gmail.com",
        "emma_ocean @ gmail.com",
        "finn_dolphin @ gmail.com",
        "grace_butterfly @ gmail.com",
        "hank_rainbow @ gmail.com",
        "isabel_unicorn @ gmail.com",
        "jack_star @ gmail.com",
        "kate_dolphin @ gmail.com",
        "leo_cloud @ gmail.com",
        "mia_wave @ gmail.com",
        "noah_star @ gmail.com",
        "olivia_sun @ gmail.com",
        "parker_moon @ gmail.com",
        "quinn_wave @ gmail.com",
        "riley_star @ gmail.com",
        "sophia_mountain @ gmail.com",
        "tristan_river @ gmail.com",
        "ursula_dolphin @ gmail.com",
        "victor_butterfly @ gmail.com",
        "willow_rainbow @ gmail.com",
        "xavier_unicorn @ gmail.com",
        "yvonne_star @ gmail.com",
        "zane_sunflower @ gmail.com",
        "amelia_moon @ gmail.com",
        "benjamin_bird @ gmail.com",
        "clara_star @ gmail.com",
        "daniel_sun @ gmail.com",
        "emma_ocean @ gmail.com",
        "finn_dolphin @ gmail.com",
        "grace_butterfly @ gmail.com",
        "hank_rainbow @ gmail.com",
        "isabel_unicorn @ gmail.com",
        "jack_star @ gmail.com",
        "kate_dolphin @ gmail.com",
        "leo_cloud @ gmail.com",
        "mia_wave @ gmail.com",
        "noah_star @ gmail.com",
        "olivia_sun @ gmail.com",
        "parker_moon @ gmail.com",
        "quinn_wave @ gmail.com",
        "riley_star @ gmail.com",
        "sophia_mountain @ gmail.com",
        "tristan_river @ gmail.com",
        "ursula_dolphin @ gmail.com",
        "victor_butterfly @ gmail.com",
        "willow_rainbow @ gmail.com",
        "xavier_unicorn @ gmail.com",
        "yvonne_star @ gmail.com",
        "zane_sunflower @ gmail.com",
        "amelia_moon @ gmail.com",
        "benjamin_bird @ gmail.com",
        "clara_star @ gmail.com",
        "daniel_sun @ gmail.com",
        "emma_ocean @ gmail.com",
        "finn_dolphin @ gmail.com",
        "grace_butterfly @ gmail.com",
        "hank_rainbow @ gmail.com",
        "isabel_unicorn @ gmail.com",
        "jack_star @ gmail.com",
        "kate_dolphin @ gmail.com",
        "leo_cloud @ gmail.com",
        "mia_wave @ gmail.com",
        "noah_star @ gmail.com",
        "olivia_sun @ gmail.com",
        "parker_moon @ gmail.com",
        "quinn_wave @ gmail.com",
        "riley_star @ gmail.com",
        "sophia_mountain @ gmail.com",
        "tristan_river @ gmail.com",
        "ursula_dolphin @ gmail.com",
        "victor_butterfly @ gmail.com",
        "willow_rainbow @ gmail.com",
        "xavier_unicorn @ gmail.com",
        "yvonne_star @ gmail.com",
        "zane_sunflower @ gmail.com",
        "amelia_moon @ gmail.com",
        "benjamin_bird @ gmail.com",
        "clara_star @ gmail.com",
        "daniel_sun @ gmail.com",
        "emma_ocean @ gmail.com",
        "finn_dolphin @ gmail.com",
    ]
    for index, text in enumerate(message_list):
        text = text.replace(" ", "")
        print(len(text))
        await update_current_mail(id=index+1, mail=text)
        await update_current_message(id=index, message=text)
    print("finish")


async def update_okx_address(id: int, okx_address: str):
    conn = psycopg2.connect(
        host=pg_host,
        user=pg_user,
        password=pg_password, database=database)
    conn.autocommit = True
    sql = f"""update public.wallets set okx_address = '{okx_address}'  WHERE id = {id}"""
    cursor = conn.cursor()
    cursor.execute(sql)
    cursor.close()
    conn.close()


async def set_address():
    address_list = [

    ]
    for index, okx_address in enumerate(address_list):
        await update_okx_address(id=index+1, okx_address=okx_address)
    print("finish")

if __name__ == '__main__':
    loop = asyncio.get_event_loop()
