import os

PACKAGE_PATH = os.path.dirname(os.path.abspath(__file__))
CONTRACTS_PATH = os.path.join(PACKAGE_PATH, 'contracts')
DEFAULT_SLIPPAGE = 0.001

UNISWAP_FEE = 3000
MIN_TICK = -887272
MAX_TICK = -MIN_TICK

TICK_SPACING = {
    100: 1,
    500: 10,
    3_000: 60,
    10_000: 200
}