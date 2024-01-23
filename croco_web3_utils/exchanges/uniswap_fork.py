from functools import lru_cache
from typing import Optional, cast
from eth_typing import ChecksumAddress
from hexbytes import HexBytes
from web3.contract import AsyncContract
from web3.types import Wei
from evm_wallet import AsyncWallet
from ._uniswap_router import UniswapRouter
from ._uniswap_router_v2 import UniswapRouterV2
from ._uniswap_router_v3 import UniswapRouterV3
from evm_wallet.types import AddressLike, TokenAmount, ABI, Network
from croco_web3_utils.types import UniswapFee, TokenOrAddress
from croco_web3_utils.abc import Defi
from croco_web3_utils.globals import DEFAULT_SLIPPAGE, UNISWAP_FEE, TICK_SPACING, CONTRACTS_PATH
from croco_web3_utils.exceptions import InvalidFee
from croco_web3_utils.utils import load_contracts


class UniswapFork(Defi):
    def __init__(
            self,
            wallet: AsyncWallet,
            defi_name: str,
            router: AsyncContract,
            factory: AsyncContract,
            pool_abi: ABI,
            quoter_v2: Optional[AsyncContract] = None,
            non_fungible_position_manager: Optional[AsyncContract] = None,
            version: int = 2,
    ):
        self.__version = version
        super().__init__(wallet, defi_name, version)

        match version:
            case 2:
                self.__proxy = UniswapRouterV2(wallet, defi_name, router, factory, pool_abi)
            case 3:
                self.__proxy = UniswapRouterV3(wallet, defi_name, router, factory, quoter_v2,
                                               non_fungible_position_manager, pool_abi)

    @property
    def proxy(self) -> UniswapRouter:
        return self.__proxy

    async def swap(
            self,
            input_token: TokenOrAddress,
            output_token: TokenOrAddress,
            input_amount: TokenAmount,
            slippage: float = DEFAULT_SLIPPAGE,
            fee: UniswapFee = UNISWAP_FEE,
            recipient: Optional[AddressLike] = None,
            gas: Optional[int] = None,
            gas_price: Optional[Wei] = None
    ) -> HexBytes:
        return await self.proxy.swap(input_token, output_token, input_amount, slippage, fee, recipient, gas,
                                     gas_price)

    async def swap_output(
            self,
            input_token: TokenOrAddress,
            output_token: TokenOrAddress,
            output_amount: TokenAmount,
            slippage: float = DEFAULT_SLIPPAGE,
            fee: UniswapFee = UNISWAP_FEE,
            recipient: Optional[AddressLike] = None,
            gas: Optional[int] = None,
            gas_price: Optional[Wei] = None
    ) -> HexBytes:
        return await self.proxy.swap_output(input_token, output_token, output_amount, slippage, fee, recipient,
                                            gas, gas_price)

    async def get_pool(
            self,
            token0: AddressLike,
            token1: AddressLike,
            fee: UniswapFee = UNISWAP_FEE
    ) -> AsyncContract:
        if fee not in TICK_SPACING.keys():
            raise InvalidFee(fee)

        return await self.proxy.get_pool(token0, token1, fee)

    async def add_liquidity(
            self,
            token0: TokenOrAddress,
            token1: TokenOrAddress,
            amount0: TokenAmount,
            amount1: Optional[TokenAmount] = None,
            fee: UniswapFee = UNISWAP_FEE
    ) -> HexBytes:
        if fee not in TICK_SPACING.keys():
            raise InvalidFee(fee)

        return await self.proxy.add_liquidity(token0, token1, amount0, amount1, fee)

    async def get_output_amount(
            self,
            input_amount: TokenAmount,
            input_token: AddressLike,
            output_token: AddressLike,
            slippage: float = 0.0
    ) -> TokenAmount:
        output_amount = await self.proxy.get_output_amount(input_amount, input_token, output_token)
        return int(output_amount * (1 - slippage))

    async def get_exchange_rate(
            self,
            token0: AddressLike,
            token1: AddressLike,
    ) -> float:
        """Get the token0/token1 exchange rate"""
        return await self.proxy.get_exchange_rate(token0, token1)

    async def get_eth_per_token(
            self,
            token: AddressLike
    ) -> float:
        """Get the token token/ETH exchange rate"""
        return await self.proxy.get_eth_per_token(token)

    @lru_cache
    async def get_weth_address(self, network: Optional[Network] = None) -> ChecksumAddress:
        current_network = self.network['network']
        network = cast(Network, network)

        if network and network != current_network:
            router = load_contracts(
                self.provider,
                self._defi_name,
                network,
                CONTRACTS_PATH,
                3
            )['router']
            weth = await router.functions.WETH9().call()
        else:
            weth = await self.proxy.get_weth_address()

        return weth
