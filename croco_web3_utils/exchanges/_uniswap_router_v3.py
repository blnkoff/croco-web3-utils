import math
from async_lru import alru_cache
from eth_typing import ChecksumAddress
from web3.contract import AsyncContract
from web3.contract.contract import ContractFunction
from web3.types import Wei
from typing import Optional, Any
from evm_wallet import AsyncWallet
from hexbytes import HexBytes
from evm_wallet.types import TokenAmount, AddressLike, ABI
from croco_web3_utils.types import RouterOperation, InputQuote, OutputQuote, UniswapFee, PoolData, PoolState
from croco_web3_utils.globals import DEFAULT_SLIPPAGE, UNISWAP_FEE, TICK_SPACING, MIN_TICK, MAX_TICK
from ._uniswap_router import UniswapRouter
from croco_web3_utils.exceptions import PoolNotFound
from croco_web3_utils.utils import get_deadline
from croco_web3_utils import validate_network
from evm_wallet import ZERO_ADDRESS


class UniswapRouterV3(UniswapRouter):
    def __init__(
            self,
            wallet: AsyncWallet,
            defi_name: str,
            router: AsyncContract,
            factory: AsyncContract,
            quoter_v2: AsyncContract,
            non_fungible_position_manager: AsyncContract,
            pool_abi: ABI
    ):
        super().__init__(wallet, defi_name, router, factory, pool_abi, 3)
        self._quoter_v2 = quoter_v2
        self._non_fungible_position_manager = non_fungible_position_manager

    @staticmethod
    async def __quote_single(
            operation: RouterOperation,
            handler: ContractFunction,
            amount: TokenAmount,
            input_token: AddressLike,
            output_token: AddressLike,
            fee: UniswapFee = UNISWAP_FEE,
    ) -> dict[str, Any]:
        sqrt_price_limit_x96 = 0

        amount_key = 'amountIn' if operation == 'input' else 'amountOut'

        params = {
            'tokenIn': input_token,
            'tokenOut': output_token,
            'fee': fee,
            amount_key: amount,
            'sqrtPriceLimitX96': sqrt_price_limit_x96
        }

        response = await handler(params).call()

        amount_key = 'amount_out' if operation == 'input' else 'amount_in'

        quote = {
            amount_key: response[0],
            'sqrt_price_x96_after': response[1],
            'initialized_ticks_crossed': response[2],
            'gas_estimate': response[3]
        }

        return quote

    async def _quote_exact_input_single(
            self,
            input_amount: TokenAmount,
            input_token: AddressLike,
            output_token: AddressLike,
            fee: UniswapFee = UNISWAP_FEE,
    ) -> InputQuote:
        quoter = self._quoter_v2
        handler = quoter.functions.quoteExactInputSingle
        quote = await self.__quote_single('input', handler, input_amount, input_token, output_token, fee)

        quote = InputQuote(**quote)
        return quote

    async def _quote_exact_output_single(
            self,
            output_amount: TokenAmount,
            input_token: AddressLike,
            output_token: AddressLike,
            fee: UniswapFee = UNISWAP_FEE,
    ) -> OutputQuote:
        quoter = self._quoter_v2
        handler = quoter.functions.quoteExactOutputSingle
        quote = await self.__quote_single('output', handler, output_amount, input_token, output_token, fee)

        quote = OutputQuote(**quote)
        return quote

    async def _get_min_output_amount(
            self,
            input_amount: TokenAmount,
            input_token: AddressLike,
            output_token: AddressLike,
            slippage: float = DEFAULT_SLIPPAGE,
            fee: UniswapFee = UNISWAP_FEE
    ) -> TokenAmount:
        quote = await self._quote_exact_input_single(input_amount, input_token, output_token, fee)
        output_amount = quote['amount_out']
        min_output_amount = int(output_amount * (1 - slippage))
        return min_output_amount

    async def _get_max_input_amount(
            self,
            output_amount: TokenAmount,
            input_token: AddressLike,
            output_token: AddressLike,
            slippage: float = DEFAULT_SLIPPAGE,
            fee: UniswapFee = UNISWAP_FEE
    ) -> TokenAmount:
        quote = await self._quote_exact_output_single(output_amount, input_token, output_token, fee)
        input_amount = quote['amount_in']
        max_input_amount = int(input_amount * (1 + slippage))
        return max_input_amount

    @alru_cache()
    async def get_weth_address(self) -> ChecksumAddress:
        address = await self._router.functions.WETH9().call()
        return address

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
        wallet = self.wallet
        sqrt_price_limit_x96 = 0
        input_token = await self.get_weth_address()
        min_amount_out = await self._get_min_output_amount(input_amount, input_token, output_token, slippage, fee)
        params = {
            "tokenIn": input_token,
            "tokenOut": output_token,
            "fee": fee,
            "recipient": recipient,
            "amountIn": input_amount,
            "amountOutMinimum": min_amount_out,
            "sqrtPriceLimitX96": sqrt_price_limit_x96,
        }
        print(params)
        closure = self._router.functions.exactInputSingle(params)
        return await wallet.build_and_transact(closure, input_amount)

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
    async def get_pool(
            self,
            token0: AddressLike,
            token1: AddressLike,
            fee: UniswapFee = UNISWAP_FEE
    ) -> AsyncContract:
        token0 = self.provider.to_checksum_address(token0)
        token1 = self.provider.to_checksum_address(token1)

        pool_address = await self._factory.functions.getPool(token0, token1, fee).call()
        pool_address = self.provider.to_checksum_address(pool_address)

        if pool_address == ZERO_ADDRESS:
            raise PoolNotFound(token0, token1)

        pool_abi = self._pool_abi

        pool = self.provider.eth.contract(address=pool_address, abi=pool_abi)
        return pool

    @validate_network
    async def _add_liquidity(
            self,
            token0: AddressLike,
            token1: AddressLike,
            amount0: TokenAmount,
            amount1: Optional[TokenAmount] = None,
            fee: UniswapFee = UNISWAP_FEE
    ) -> HexBytes:
        if not amount1:
            amount1 = await self._get_min_output_amount(amount0, token0, token1, 0)

        return await self._mint_liquidity(token0, token1, amount0, amount1, fee, False)

    @validate_network
    async def _add_liquidity_eth(
            self,
            token1: AddressLike,
            amount1: TokenAmount,
            amount0: Optional[TokenAmount] = None,
            fee: UniswapFee = UNISWAP_FEE
    ) -> HexBytes:
        weth = await self.get_weth_address()

        if not amount0:
            amount0 = await self._get_min_output_amount(amount1, token1, weth, 0)

        return await self._mint_liquidity(weth, token1, amount0, amount1, fee)

    async def _mint_liquidity(
            self,
            token0: AddressLike,
            token1: AddressLike,
            amount0: TokenAmount,
            amount1: TokenAmount,
            fee: UniswapFee = UNISWAP_FEE,
            payable: bool = True
    ) -> HexBytes:
        wallet = self.wallet

        pool = await self.get_pool(token0, token1, fee)

        tick_lower, tick_upper = self.__get_tick_range(fee)

        *_, unlocked = await self._get_pool_state(pool)

        if not unlocked:
            sqrt_price_x96 = self.__get_sqrt_ratio_x96(amount0, amount1)
            closure = pool.functions.initialize(sqrt_price_x96)
            await wallet.build_and_transact(closure)

        nft_manager = self._non_fungible_position_manager

        await wallet.approve(token0, nft_manager.address, amount0)
        await wallet.approve(token1, nft_manager.address, amount0)

        params = {
            'token0': token0,
            'token1': token1,
            'fee': fee,
            'tickLower': tick_lower,
            'tickUpper': tick_upper,
            'amount0Desired': amount0,
            'amount1Desired': amount1,
            'amount0Min': 0,
            'amount1Min': 0,
            'recipient': wallet.public_key,
            'deadline': get_deadline()
        }
        
        value = amount0 if payable else 0

        tx_data = nft_manager.functions.mint(params).build_transaction(
            wallet.build_transaction_params(value)
        )['data']

        closure = nft_manager.functions.multicall(tx_data)

        return await wallet.build_and_transact(closure, value)

    @staticmethod
    def __get_sqrt_ratio_x96(amount_0: int, amount_1: int) -> int:
        numerator = amount_1 << 192
        denominator = amount_0
        ratio_x192 = numerator // denominator
        return int(math.sqrt(ratio_x192))

    @staticmethod
    def __get_tick_range(fee: int) -> tuple[int, int]:
        tick_spacing = TICK_SPACING[fee]

        min_tick = -(MIN_TICK // -tick_spacing) * tick_spacing
        max_tick = (MAX_TICK // tick_spacing) * tick_spacing

        return min_tick, max_tick

    @staticmethod
    async def _get_pool_data(pool: AsyncContract) -> PoolData:
        """
        Fetch on-chain pool data.
        """
        pool_data = PoolData(
            factory=await pool.functions.factory().call(),
            token0=await pool.functions.token0().call(),
            token1=await pool.functions.token1().call(),
            fee=await pool.functions.fee().call(),
            tick_spacing=await pool.functions.tickSpacing().call(),
            max_liquidity_per_tick=await pool.functions.maxLiquidityPerTick().call(),
        )
        return pool_data

    @staticmethod
    async def _get_pool_state(pool: AsyncContract) -> PoolState:
        """
        Fetch on-chain pool state.
        """
        liquidity = await pool.functions.liquidity().call()
        slot = await pool.functions.slot0().call()
        pool_state = PoolState(
            liquidity=liquidity,
            sqrt_price_x96=slot[0],
            tick=slot[1],
            observation_index=slot[2],
            observation_cardinality=slot[3],
            observation_cardinality_next=slot[4],
            fee_protocol=slot[5],
            unlocked=slot[6]
        )

        return pool_state
