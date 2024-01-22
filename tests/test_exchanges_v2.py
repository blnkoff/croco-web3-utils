import pytest
from croco_web3_utils.exchanges import *


class _TestRouterV2:
    @pytest.mark.tx
    @pytest.mark.asyncio
    async def test_eth_to_tokens_input(self, wallet, eth_amount, router, sub_token, native_token):
        return await router.swap(native_token, sub_token, eth_amount)

    @pytest.mark.tx
    @pytest.mark.asyncio
    async def test_tokens_to_tokens_input(self, wallet, eth_amount, router,  sub_token):
        output_token = '0x6B175474E89094C44Da98b954EedeAC495271d0F'
        return await router.swap(eth_amount, sub_token, output_token)

    @pytest.mark.tx
    @pytest.mark.asyncio
    async def test_tokens_to_eth_input(self, wallet, eth_amount, router,  sub_token, native_token):
        return await router.swap(eth_amount, sub_token, native_token)

    @pytest.mark.tx
    @pytest.mark.asyncio
    async def test_tokens_to_eth_output(self, wallet, eth_amount, router,  sub_token, native_token):
        return await router.swap_output(eth_amount, sub_token, native_token)


class TestUniswap(_TestRouterV2):
    @pytest.fixture(scope="class")
    def wallet(self, make_wallet):
        return make_wallet('Goerli')

    @pytest.fixture
    def sub_token(self):
        uni_address = '0x1f9840a85d5af5bf1d1762f925bdaddc4201f984'
        return uni_address

    @pytest.fixture
    def router(self, wallet):
        return Uniswap(wallet)


class TestPancakeSwap(_TestRouterV2):
    @pytest.fixture(scope="class")
    def wallet(self, make_wallet):
        return make_wallet('Goerli')

    @pytest.fixture
    def router(self, wallet):
        return PancakeSwap(wallet)
    
    @pytest.fixture
    def sub_token(self):
        dai_address = '0x07865c6E87B9F70255377e024ace6630C1Eaa37F'
        return dai_address
