import os
import json
from web3 import AsyncWeb3
from typing import Optional
from typing import Literal, get_args
from python_extras import in_literal
from croco_web3_utils.exceptions import InvalidToken
from croco_web3_utils.exceptions import ContractNotFound
from functools import wraps, lru_cache
from evm_wallet.types import Network
from croco_web3_utils.types import ContractMap


def _pascal_to_snake(s: str) -> str:
    """
    Convert a string in PascalCase to snake_case.
    """
    return ''.join(['_' + i.lower() if i.isupper() and idx != 0 else i.lower() for idx, i in enumerate(s)]).lstrip('_')


@lru_cache()
def load_contracts(
        provider: AsyncWeb3,
        defi: str,
        network: Network | str,
        contracts_path: str,
        version: Optional[int] = None
) -> ContractMap:
    folder_name = _pascal_to_snake(defi)
    path = os.path.join(contracts_path, folder_name)

    if version:
        path += f'/v{version}'

    contract_data = {}
    with open(f"{path}/contracts.json") as file:
        content = json.load(file)
        contract_names = content.keys()

        for name in contract_names:
            contract_content = content[name]
            if 'address' in contract_content:
                addresses = content[name]['address']
                if network not in addresses:
                    raise ContractNotFound(defi, network, addresses.keys())

                contract_data[name] = {'address': addresses[network]}

    for name in contract_names:
        with open(f'{path}/{name}.abi') as file:
            abi = json.load(file)
            if name in contract_data:
                contract_data[name]['abi'] = abi
            else:
                contract_data[f"{name}_abi"] = {'abi': abi}

    contracts = {}
    for key, value in contract_data.items():
        abi = value['abi']

        address = value.get('address')
        contracts[key] = provider.eth.contract(address=address, abi=abi) if address else abi

    return contracts


def validate_network(func):
    @wraps(func)
    def wrapper(self, *args, **kwargs):
        network = self.network
        wallet = self.wallet

        if network != wallet.network:
            defi = self._defi_name or self.__class__.__name__

            try:
                version = self.version
            except AttributeError:
                version = None

            contracts = load_contracts(wallet.provider, defi, wallet.network['network'], version)

            for key, value in contracts.items():
                setattr(self, f'_{key}', value)

            self._network = wallet.network

        return func(self, *args, **kwargs)

    return wrapper


def validate_token(
        token: str,
        token_literal: Literal,
        network: str,
        defi: str
) -> None:
    if not in_literal(token, token_literal):
        raise InvalidToken(token, network, defi, get_args(token_literal))
