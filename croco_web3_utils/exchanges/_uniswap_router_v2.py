from async_lru import alru_cache
from eth_typing import ChecksumAddress
from web3.contract import AsyncContract
from web3.contract.contract import ContractFunction
from web3.types import Wei
from typing import Optional
from evm_wallet import AsyncWallet
from hexbytes import HexBytes
from evm_wallet.types import TokenAmount, AddressLike, ABI
from croco_web3_utils.types import RouterOperation, UniswapFee
from croco_web3_utils.globals import DEFAULT_SLIPPAGE, UNISWAP_FEE
from ._uniswap_router import UniswapRouter
from croco_web3_utils.utils import get_deadline
from croco_web3_utils import validate_network


class UniswapRouterV2(UniswapRouter):
    def __init__(
            self,
            wallet: AsyncWallet,
            defi_name: str,
            router: AsyncContract,
            factory: AsyncContract,
            pool_abi: ABI,
    ):
        super().__init__(wallet, defi_name, router, factory, pool_abi, 2)

    async def _get_min_output_amount(
            self,
            input_amount: TokenAmount,
            input_token: AddressLike,
            output_token: AddressLike,
            slippage: float = DEFAULT_SLIPPAGE,
            fee: UniswapFee = UNISWAP_FEE
    ) -> TokenAmount:
        weth = await self.get_weth_address()
        if input_token == weth or output_token == weth:
            path = [input_token, output_token]
        else:
            path = [input_token, weth, output_token]

        amounts_out = await self._get_output_amounts(input_amount, path)
        amount_out = amounts_out[-1]
        min_amount_out = int(amount_out * (1 - slippage))
        return min_amount_out

    async def _get_output_amounts(self, input_amount: TokenAmount, path: list[str]) -> list[TokenAmount]:
        provider = self.provider
        path = [provider.to_checksum_address(address) for address in path]
        amounts_out = await self._router.functions.getAmountsOut(input_amount, path).call()
        return amounts_out

    async def _get_max_input_amount(
            self,
            output_amount: TokenAmount,
            input_token: AddressLike,
            output_token: AddressLike,
            slippage: float = DEFAULT_SLIPPAGE,
            fee: UniswapFee = UNISWAP_FEE
    ) -> TokenAmount:
        weth = await self.get_weth_address()
        if input_token == weth or output_token == weth:
            path = [input_token, output_token]
        else:
            path = [input_token, weth, output_token]

        amounts_in = await self._get_input_amounts(output_amount, path)
        amount_in = amounts_in[0]
        max_amount_in = int(amount_in * (1 + slippage))
        return max_amount_in

    async def _get_input_amounts(self, output_amount: TokenAmount, path: list[str]) -> list[TokenAmount]:
        provider = self.provider
        path = [provider.to_checksum_address(address) for address in path]
        amounts_in = await self._router.functions.getAmountsIn(output_amount, path).call()

        return amounts_in

    @alru_cache()
    async def get_weth_address(self) -> ChecksumAddress:
        address = await self._router.functions.WETH().call()
        return address

    async def __swap(
            self,
            operation: RouterOperation,
            handler: ContractFunction,
            amount: TokenAmount,
            required_amount: TokenAmount,
            path: list[str],
            recipient: Optional[str] = None,
            gas: Optional[int] = None,
            gas_price: Optional[Wei] = None,
            payable: bool = False
    ) -> HexBytes:
        provider = self.provider
        wallet = self.wallet
        if not recipient:
            recipient = wallet.public_key

        path = [provider.to_checksum_address(address) for address in path]

        handler_arguments = [required_amount, path, recipient, get_deadline()]

        if not payable:
            handler_arguments.insert(0, amount)
            eth_amount = 0
        elif operation == 'output':
            eth_amount = required_amount
        else:
            eth_amount = amount

        closure = handler(*handler_arguments)
        return await wallet.build_and_transact(closure, eth_amount, gas, gas_price)

    async def __input_swap(
            self,
            handler: ContractFunction,
            input_amount: TokenAmount,
            path: list[str],
            slippage: float = DEFAULT_SLIPPAGE,
            fee: UniswapFee = UNISWAP_FEE,
            recipient: Optional[str] = None,
            gas: Optional[int] = None,
            gas_price: Optional[Wei] = None,
            payable: bool = False
    ) -> HexBytes:
        input_token = path[0]
        output_token = path[-1]
        min_amount_out = await self._get_min_output_amount(input_amount, input_token, output_token, slippage, fee)
        return await self.__swap('input', handler, input_amount, min_amount_out, path,
                                 recipient, gas, gas_price, payable)

    async def __output_swap(
            self,
            handler: ContractFunction,
            output_amount: TokenAmount,
            path: list[str],
            slippage: float = DEFAULT_SLIPPAGE,
            fee: UniswapFee = UNISWAP_FEE,
            recipient: Optional[str] = None,
            gas: Optional[int] = None,
            gas_price: Optional[Wei] = None,
            payable: bool = False
    ) -> HexBytes:
        input_token = path[0]
        output_token = path[1]
        max_amount_in = await self._get_max_input_amount(output_amount, input_token, output_token, slippage, fee)
        return await self.__swap('output', handler, output_amount, max_amount_in, path,
                                 recipient, gas, gas_price, payable)

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
        contract = self._router
        handler = contract.functions.swapExactTokensForTokens
        weth = await self.get_weth_address()
        path = [input_token, weth, output_token]
        return await self.__input_swap(handler, input_amount, path, slippage, fee, recipient, gas, gas_price)

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
        contract = self._router
        handler = contract.functions.swapExactETHForTokens
        weth = await self.get_weth_address()
        path = [weth, output_token]
        return await self.__input_swap(handler, input_amount, path, slippage, fee, recipient, gas, gas_price,
                                       True)

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
        contract = self._router
        handler = contract.functions.swapExactTokensForETH
        weth = await self.get_weth_address()
        path = [input_token, weth]
        return await self.__input_swap(handler, input_amount, path, slippage, fee, recipient, gas, gas_price)

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
        contract = self._router
        handler = contract.functions.swapTokensForExactETH
        weth = await self.get_weth_address()
        path = [input_token, weth]
        return await self.__output_swap(handler, output_amount, path, slippage, fee, recipient, gas, gas_price)

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
        contract = self._router
        handler = contract.functions.swapETHForExactTokens
        weth = await self.get_weth_address()
        path = [weth, output_token]
        return await self.__output_swap(handler, output_amount, path, slippage, fee, recipient, gas, gas_price,
                                        True)

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
        contract = self._router
        handler = contract.functions.swapTokensForExactTokens
        weth = await self.get_weth_address()
        path = [input_token, weth, output_token]
        return await self.__output_swap(handler, output_amount, path, slippage, fee, recipient, gas, gas_price)

    @validate_network
    async def get_pool(
            self,
            token0: AddressLike,
            token1: AddressLike,
            fee: UniswapFee = UNISWAP_FEE
    ) -> AsyncContract:
        pass

    @validate_network
    async def _add_liquidity(
            self,
            token0: AddressLike,
            token1: AddressLike,
            amount0: TokenAmount,
            amount1: Optional[TokenAmount] = None,
            fee: UniswapFee = UNISWAP_FEE
    ) -> HexBytes:
        pass

    @validate_network
    async def _add_liquidity_eth(
            self,
            token0: AddressLike,
            amount0: TokenAmount,
            amount1: Optional[TokenAmount] = None,
            fee: UniswapFee = UNISWAP_FEE
    ) -> HexBytes:
        pass
