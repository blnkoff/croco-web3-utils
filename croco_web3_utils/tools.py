from eth_typing import ChecksumAddress
from evm_wallet import AsyncWallet, Wallet, ZERO_ADDRESS
from evm_wallet.types import TokenAmount
from web3 import AsyncWeb3
from web3.types import Wei
from croco_web3_utils.types import TokenOrAddress
from croco_web3_utils.exchanges.exchanges import Uniswap


def validate_route(
        wallet: AsyncWallet | Wallet,
        input_token: TokenOrAddress,
        input_amount: TokenAmount,
        output_token: TokenOrAddress,
        to_weth: bool = True
) -> tuple[ChecksumAddress, Wei, ChecksumAddress]:
    uniswap = Uniswap(wallet)
    if wallet.is_native_token(input_token):
        value = input_amount
        if to_weth:
            input_token = uniswap.get_weth_address()
        else:
            input_token = ZERO_ADDRESS
    else:
        value = 0
        input_token = AsyncWeb3.to_checksum_address(input_token)

    if wallet.is_native_token(output_token):
        if to_weth:
            output_token = uniswap.get_weth_address()
        else:
            output_token = ZERO_ADDRESS
    else:
        output_token = AsyncWeb3.to_checksum_address(output_token)

    return input_token, value, output_token
