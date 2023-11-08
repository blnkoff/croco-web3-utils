from typing import Any

from ether_wallet.types import Network


class ContractNotFound(Exception):
    """Raised when contract is not found in a specific network"""

    def __init__(self, defi: str, destination_network: Network, supported_networks: list[Network]):
        super().__init__(f"Contract is not found in {destination_network}. {defi} supports the following networks: "
                         f"{', '.join(supported_networks)}")


class InvalidToken(ValueError):
    """Raised when token is not supported in a specific network in a contract"""

    def __init__(self, token: Any, network: str, defi: str):
        super().__init__(f"Token {token} is not supported in {network} for using in {defi}")
