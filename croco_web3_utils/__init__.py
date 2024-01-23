"""
croco-web3-utils
~~~~~~~~~~~~~~
The package containing utilities to develop Web3-based projects

:copyright: (c) 2023 by Alexey
:license: MIT, see LICENSE for more details.
"""

from .abc import Defi
from .utils import load_contracts, get_deadline, validate_route
from .exchanges import Uniswap, PancakeSwap
from .types import ContractMap, ContractVersion, TokenOrAddress
from .exceptions import InvalidToken
