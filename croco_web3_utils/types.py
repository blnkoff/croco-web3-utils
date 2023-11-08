from typing import Literal, Union
from ether_wallet.types import ABI, AddressLike
from web3.contract import AsyncContract, Contract

ContractVersion = Literal[2, 3]
ContractMap = dict[str, AsyncContract | ABI | Contract]
TokenOrAddress = Union[AddressLike, str]
