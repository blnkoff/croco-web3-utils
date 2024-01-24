"""
croco-web3-utils
~~~~~~~~~~~~~~
The package containing utilities to develop Web3-based projects

:copyright: (c) 2023 by Alexey
:license: MIT, see LICENSE for more details.
"""

from .abc import Defi
from .utils import load_contracts, get_deadline, validate_network
from .tools import validate_route, validate_token
from .types import ContractMap, TokenOrAddress
from .exceptions import InvalidToken, InvalidToken
