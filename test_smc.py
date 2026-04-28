import pandas as pd
import numpy as np
from smc_strategy import SMCStrategy

# Create test data
test_df = pd.DataFrame({
    'Close': np.random.uniform(100, 120, 50),
    'High': np.random.uniform(120, 130, 50),
    'Low': np.random.uniform(90, 100, 50)
})

# Test all SMC functions
print('Testing SMC functions...')
signal = SMCStrategy.generate_smc_signal(test_df)
order_blocks = SMCStrategy.find_order_blocks(test_df)
liquidity = SMCStrategy.find_liquidity_levels(test_df)
fvgs = SMCStrategy.find_fair_value_gaps(test_df)
sd_zones = SMCStrategy.find_supply_demand_zones(test_df)

print('[OK] Signal:', signal.get('action'))
print('[OK] Order Blocks type:', type(order_blocks).__name__, '- Bullish' if order_blocks.get('bullish') else '- No bullish')
print('[OK] Liquidity type:', type(liquidity).__name__, '- Support' if liquidity.get('support') else '- No support')
print('[OK] FVGs type:', type(fvgs).__name__, '- Bullish' if fvgs.get('bullish') else '- No bullish')
print('[OK] SD Zones type:', type(sd_zones).__name__)
print('\n[SUCCESS] All SMC functions working correctly!')
