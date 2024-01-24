from typing import Union
from evm_wallet.types import ABI, AddressLike
from web3.contract import AsyncContract, Contract

ContractMap = dict[str, AsyncContract | ABI | Contract]
TokenOrAddress = Union[AddressLike, str]
