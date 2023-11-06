from abc import ABC
from typing import Optional
from web3 import AsyncWeb3
from ether_wallet import AsyncWallet, NetworkInfo, Wallet
from .types import ContractVersion


class Defi(ABC):
    def __init__(
            self,
            wallet: AsyncWallet | Wallet,
            defi_name: str,
            version: Optional[ContractVersion] = None
    ):
        self.__wallet = wallet
        self._network = wallet.network
        self._defi_name = defi_name
        self._version = version

    @property
    def wallet(self) -> AsyncWallet | Wallet:
        return self.__wallet

    @property
    def network(self) -> NetworkInfo:
        return self._network

    @property
    def provider(self) -> AsyncWeb3:
        return self.wallet.provider

    @property
    def version(self) -> ContractVersion | None:
        return self._version
