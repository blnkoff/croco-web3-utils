from evm_wallet import AsyncWallet
from web3 import AsyncWeb3
from web3.types import Wei
from croco_web3_utils.exceptions import InvalidFee
from hexbytes import HexBytes
from croco_web3_utils.globals import DEFAULT_SLIPPAGE, UNISWAP_FEE, TICK_SPACING
from croco_web3_utils import validate_network, Defi, ContractVersion
from typing import Optional
from abc import abstractmethod, ABC
from eth_typing import ChecksumAddress
from web3.contract import AsyncContract
from evm_wallet.types import TokenAmount, AddressLike, ABI
from croco_web3_utils.types import TokenOrAddress, UniswapFee


class UniswapRouter(Defi, ABC):
    def __init__(
            self,
            wallet: AsyncWallet,
            defi_name: str,
            router: AsyncContract,
            factory: AsyncContract,
            pool_abi: ABI,
            version: ContractVersion
    ):
        super().__init__(wallet, defi_name, version)
        self._router = router

        self._factory = factory
        self._pool_abi = pool_abi
        self.__version = version

    @abstractmethod
    async def _get_max_input_amount(
            self,
            output_amount: TokenAmount,
            input_token: AddressLike,
            output_token: AddressLike,
            slippage: float = DEFAULT_SLIPPAGE,
            fee: UniswapFee = UNISWAP_FEE
    ) -> TokenAmount:
        pass

    @abstractmethod
    async def _get_min_output_amount(
            self,
            input_amount: TokenAmount,
            input_token: AddressLike,
            output_token: AddressLike,
            slippage: float = DEFAULT_SLIPPAGE,
            fee: UniswapFee = UNISWAP_FEE
    ) -> TokenAmount:
        pass

    @abstractmethod
    async def _get_weth_address(self) -> ChecksumAddress:
        pass

    @abstractmethod
    async def _tokens_to_tokens_input(
            self,
            input_amount: TokenAmount,
            input_token: AddressLike,
            output_token: AddressLike,
            slippage: float = DEFAULT_SLIPPAGE,
            fee: UniswapFee = UNISWAP_FEE,
            recipient: Optional[str] = None,
            gas: Optional[int] = None,
            gas_price: Optional[Wei] = None
    ) -> HexBytes:
        pass

    @abstractmethod
    @validate_network
    async def _eth_to_tokens_input(
            self,
            input_amount: TokenAmount,
            output_token: AddressLike,
            slippage: float = DEFAULT_SLIPPAGE,
            fee: UniswapFee = UNISWAP_FEE,
            recipient: Optional[str] = None,
            gas: Optional[int] = None,
            gas_price: Optional[Wei] = None
    ) -> HexBytes:
        pass

    @abstractmethod
    async def _tokens_to_eth_input(
            self,
            input_amount: TokenAmount,
            input_token: AddressLike,
            slippage: float = DEFAULT_SLIPPAGE,
            fee: UniswapFee = UNISWAP_FEE,
            recipient: Optional[str] = None,
            gas: Optional[int] = None,
            gas_price: Optional[Wei] = None
    ) -> HexBytes:
        pass

    @abstractmethod
    async def _tokens_to_eth_output(
            self,
            output_amount: TokenAmount,
            input_token: AddressLike,
            slippage: float = DEFAULT_SLIPPAGE,
            fee: UniswapFee = UNISWAP_FEE,
            recipient: Optional[str] = None,
            gas: Optional[int] = None,
            gas_price: Optional[Wei] = None
    ) -> HexBytes:
        pass

    @abstractmethod
    async def _eth_to_tokens_output(
            self,
            output_amount: TokenAmount,
            output_token: AddressLike,
            slippage: float = DEFAULT_SLIPPAGE,
            fee: UniswapFee = UNISWAP_FEE,
            recipient: Optional[str] = None,
            gas: Optional[int] = None,
            gas_price: Optional[Wei] = None
    ) -> HexBytes:
        pass

    @abstractmethod
    async def _tokens_to_tokens_output(
            self,
            output_amount: TokenAmount,
            input_token: AddressLike,
            output_token: AddressLike,
            slippage: float = DEFAULT_SLIPPAGE,
            fee: UniswapFee = UNISWAP_FEE,
            recipient: Optional[str] = None,
            gas: Optional[int] = None,
            gas_price: Optional[Wei] = None
    ) -> HexBytes:
        pass

    @validate_network
    async def add_liquidity(
            self,
            token0: TokenOrAddress,
            token1: TokenOrAddress,
            amount0: TokenAmount,
            amount1: Optional[TokenAmount] = None,
            fee: UniswapFee = UNISWAP_FEE
    ) -> HexBytes:
        wallet = self.wallet
        weth = await self._get_weth_address()

        if not amount1:
            amount1 = await self._get_min_output_amount(amount0, weth, token1, 0)

        if wallet.is_native_token(token0):
            return await self._add_liquidity_eth(token1, amount1, amount0, fee)
        elif wallet.is_native_token(token1):
            return await self._add_liquidity_eth(token0, amount0, amount1, fee)
        else:
            return await self._add_liquidity(token0, token1, amount0, amount1, fee)

    @abstractmethod
    async def _add_liquidity(
            self,
            token0: AddressLike,
            token1: AddressLike,
            amount0: TokenAmount,
            amount1: Optional[TokenAmount] = None,
            fee: UniswapFee = UNISWAP_FEE
    ) -> HexBytes:
        pass

    @abstractmethod
    async def _add_liquidity_eth(
            self,
            token0: AddressLike,
            amount0: TokenAmount,
            amount1: Optional[TokenAmount] = None,
            fee: UniswapFee = UNISWAP_FEE
    ) -> HexBytes:
        pass

    @abstractmethod
    @validate_network
    async def get_pool(
            self,
            token0: AddressLike,
            token1: AddressLike,
            fee: UniswapFee = UNISWAP_FEE
    ) -> AsyncContract:
        pass

    @validate_network
    async def get_token_amount(
            self,
            amount0: TokenAmount,
            token0: AddressLike,
            token1: AddressLike
    ) -> TokenAmount:
        return await self._get_min_output_amount(amount0, token0, token1, 0)

    @validate_network
    async def get_exchange_rate(
            self,
            token0: AddressLike,
            token1: AddressLike,
    ) -> float:
        """Get the token0/token1 exchange rate"""
        output_amount = await self._get_min_output_amount(1, token0, token1)
        exchange_rate = 1/output_amount
        return exchange_rate

    @validate_network
    async def get_eth_per_token(
            self,
            token: AddressLike
    ) -> float:
        """Get the token token/ETH exchange rate"""
        weth = await self._get_weth_address()
        amount = AsyncWeb3.to_wei(1, 'ether')
        eth_price = await self._get_min_output_amount(amount, token, weth)**(-18)
        return eth_price

    @validate_network
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
        if fee not in TICK_SPACING.keys():
            raise InvalidFee(fee)

        recipient = self.wallet.public_key if not recipient else recipient
        wallet = self.wallet

        if wallet.is_native_token(input_token):
            output_address = self.provider.to_checksum_address(output_token)
            tx_hash = await self._eth_to_tokens_input(input_amount, output_address, slippage, fee, recipient, gas,
                                                      gas_price)
        elif wallet.is_native_token(output_token):
            input_address = self.provider.to_checksum_address(input_token)
            await wallet.approve(input_address, self._router.address, input_amount)
            tx_hash = await self._tokens_to_eth_input(input_amount, input_address, slippage, fee, recipient, gas,
                                                      gas_price)
        else:
            input_address = self.provider.to_checksum_address(input_token)
            output_address = self.provider.to_checksum_address(output_token)
            await wallet.approve(input_address, self._router.address, input_amount)
            tx_hash = await self._tokens_to_tokens_input(input_amount, input_address, output_address, slippage, fee,
                                                         recipient, gas, gas_price)
        return tx_hash

    @validate_network
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
        if fee not in TICK_SPACING.keys():
            raise InvalidFee(fee)

        wallet = self.wallet
        recipient = self.wallet.public_key if not recipient else recipient

        if wallet.is_native_token(input_token):
            output_address = self.provider.to_checksum_address(output_token)
            tx_hash = await self._eth_to_tokens_output(output_amount, output_address, slippage, fee, recipient, gas,
                                                       gas_price)
        elif wallet.is_native_token(output_token):
            input_address = self.provider.to_checksum_address(input_token)
            weth = await self._get_weth_address()
            input_amount = int(output_amount * await self.get_exchange_rate(input_address, weth))
            await wallet.approve(input_address, self._router.address, input_amount)
            tx_hash = await self._tokens_to_eth_output(output_amount, input_address, slippage, fee, recipient, gas,
                                                       gas_price)
        else:
            input_address = self.provider.to_checksum_address(input_token)
            output_address = self.provider.to_checksum_address(output_token)
            input_amount = int(output_amount * await self.get_exchange_rate(input_address, output_address))
            await wallet.approve(input_address, self._router.address, input_amount)
            tx_hash = await self._tokens_to_tokens_output(output_amount, input_address, output_address, slippage, fee,
                                                          recipient, gas, gas_price)
        return tx_hash
