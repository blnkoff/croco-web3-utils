from typing import Any


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
