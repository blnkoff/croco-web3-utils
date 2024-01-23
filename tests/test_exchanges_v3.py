import pytest
from croco_web3_utils.exchanges import *


class _TestRouterV3:
    @pytest.mark.tx
    @pytest.mark.asyncio
    async def test_eth_to_tokens_input(self, wallet, eth_amount, router, sub_token, native_token):
        return await router.swap(native_token, sub_token, eth_amount)

    @pytest.mark.asyncio
    async def test_get_pool(self, router, sub_token, native_token):
        weth = await router.proxy.get_weth_address()
        pool = await router.proxy.get_pool(weth, sub_token)
        assert pool

    @pytest.mark.asyncio
    async def test_get_pool_state(self, router, sub_token):
        weth = await router.proxy.get_weth_address()
        pool = await router.proxy.get_pool(weth, sub_token)
        pool_state = await router.proxy._get_pool_state(pool)
        assert pool_state

    @pytest.mark.asyncio
    async def test_get_pool_data(self, router, sub_token):
        weth = await router.proxy.get_weth_address()
        pool = await router.proxy.get_pool(weth, sub_token)
        pool_data = await router.proxy._get_pool_data(pool)
        assert pool_data

    @pytest.mark.tx
    @pytest.mark.asyncio
    async def test_add_liquidity_eth(self, wallet, router, sub_token, eth_amount, native_token):
        return await router.add_liquidity(native_token, sub_token, eth_amount)


class TestUniswap(_TestRouterV3):
    @pytest.fixture(scope="class")
    def wallet(self, make_wallet):
        return make_wallet('BSC')

    @pytest.fixture
    def router(self, wallet):
        return Uniswap(wallet, 3)

    @pytest.fixture
    def sub_token(self):
        usdt_address = '0x55d398326f99059fF775485246999027B3197955'
        return usdt_address
