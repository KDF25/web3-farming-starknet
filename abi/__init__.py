import json
import os

""" Contract ABI """


abi_folder = os.path.join(os.path.dirname(__file__))

erc_20 = json.load(open(os.path.join(abi_folder, 'erc_20.json')))
tenkswap_abi = json.load(open(os.path.join(abi_folder, 'tenkswap.json')))
sithswap_abi = json.load(open(os.path.join(abi_folder, 'sithswap.json')))
starkexswap_abi = json.load(open(os.path.join(abi_folder, 'starkexswap.json')))
fibrousswap_abi = json.load(open(os.path.join(abi_folder, 'fibrousswap.json')))
starkverseart_abi = json.load(open(os.path.join(abi_folder, 'starkverseart.json')))
zklend_abi = json.load(open(os.path.join(abi_folder, 'zklend.json')))
argentx_abi = json.load(open(os.path.join(abi_folder, 'argentx.json')))
