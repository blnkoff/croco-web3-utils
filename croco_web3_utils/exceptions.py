from typing import Any
from evm_wallet.types import AddressLike


class ContractNotFound(ValueError):
    """Raised when contract is not found in a specific network"""

    def __init__(self, defi: str, destination_network: str, supported_networks: list[str]):
        super().__init__(f"Contract is not found in {destination_network}. {defi} supports the following networks: "
                         f"{', '.join(supported_networks)}")


class InvalidToken(TypeError):
    """Raised when token is not supported in a specific network in a contract or in a contract as a whole"""

    def __init__(self, token: Any, network: str, defi: str, supported_tokens: list[str] | tuple[str]):
        super().__init__(f"Token {token} is not supported in {network} or in a contract as a whole for "
                         f"using in {defi}. This contract supports: {', '.join(supported_tokens)}")


class InvalidRoute(ValueError):
    """Raised when provided token route is invalid"""
    def __init__(self, input_token: str, output_token: str, source_network: str, destination_network: str, defi: str):
        super().__init__(f"Token route {input_token} ({source_network}) --> {output_token} ({destination_network}) is "
                         f"not valid for {defi}")


class PoolNotFound(ValueError):
    """Raised when liquidity pool doesn't exists for particular tokens"""

    def __init__(self, token0: AddressLike, token1: AddressLike):
        super().__init__(f"0 address returned. Pool does not exist for tokens {token0} and {token1}")


class InvalidFee(TypeError):
    """Raised when fee doesn't represent one of supported levels: 0.05%, 0.3%, 1%"""

    def __init__(self, fee: Any):
        super().__init__(f"Router V3 only supports three levels of fees: 0.05%, 0.3%, 1%, that equal 500,"
                         f"3000 and 10000 respectively. You provided value - {fee}")
