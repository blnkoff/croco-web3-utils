from typing import Literal, Union, TypedDict
from evm_wallet.types import ABI, AddressLike
from web3.contract import AsyncContract, Contract

ContractMap = dict[str, AsyncContract | ABI | Contract]
TokenOrAddress = Union[AddressLike, str]

StargateToken = Literal['USDC', 'USDT', 'DAI', 'FRAX', 'USDD', 'ETH', 'sUSD', 'LUSD', 'MAI', 'METIS', 'metisUSDT']
RouterOperation = Literal['input', 'output']
UniswapFee = Literal[500, 3000, 10000]
InterestRateMode = Literal['stable', 'variable']
NumberInterestRateMode = Literal[1, 2]
UniswapVersion = Literal[2, 3]


class PoolData(TypedDict):
    factory: AddressLike
    token0: AddressLike
    token1: AddressLike
    fee: int
    tick_spacing: int
    max_liquidity_per_tick: int


class PoolState(TypedDict):
    liquidity: int
    sqrt_price_x96: int
    tick: int
    observation_index: int
    observation_cardinality: int
    observation_cardinality_next: int
    fee_protocol: int
    unlocked: int


class _QuotePart(TypedDict):
    sqrt_price_x96_after: int
    initialized_ticks_crossed: int
    gas_estimate: int


class InputQuote(_QuotePart):
    amount_out: int


class OutputQuote(_QuotePart):
    amount_in: int
