from typing import Literal
from ether_wallet.types import ABI
from web3.contract import AsyncContract, Contract

ContractVersion = Literal[2, 3]
ContractMap = dict[str, AsyncContract | ABI | Contract]