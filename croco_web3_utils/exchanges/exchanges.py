from .uniswap_fork import UniswapFork
from croco_web3_utils.types import ContractVersion
from evm_wallet import AsyncWallet
from croco_web3_utils.utils import load_contracts
from ..globals import CONTRACTS_PATH


class Uniswap(UniswapFork):
    def __init__(
            self,
            wallet: AsyncWallet,
            version: ContractVersion = 3
    ):
        contracts = load_contracts(
            wallet.provider,
            'Uniswap',
            wallet.network['network'],
            CONTRACTS_PATH,
            version
        )

        super().__init__(
            wallet=wallet,
            version=version,
            defi_name='Uniswap',
            **contracts
        )


class PancakeSwap(UniswapFork):
    def __init__(
            self,
            wallet: AsyncWallet,
            version: ContractVersion = 2
    ):
        contracts = load_contracts(
            wallet.provider,
            'PancakeSwap',
            wallet.network['network'],
            CONTRACTS_PATH,
            version
        )
        super().__init__(
            wallet=wallet,
            version=version,
            defi_name='PancakeSwap',
            **contracts
        )
