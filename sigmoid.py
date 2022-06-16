from typing import Dict, List

# import math
import numpy as np
import pandas as pd

import traceback
import logging

import utils
from scenario import Scenario
from bonding_curve import BondingCurve

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

"""
Reference:  https://medium.com/molecule-blog/designing-different-fundraising-scenarios-with-sigmoidal-token-bonding-curves-ceafc734ed97

Capital locked up in the curve collateral can generally 
be regarded as a drawback and an economic inefficiency 
when using TBCs for automated market making. Long-term 
investors not interested in making profits around price 
speculations want their money to be put to good use and 
not sit around in some smart contract on the blockchain. 
One potential way to remove funds from the buyback reserve 
to pay for actual expenses or work contributed by collaborators 
is to use different bonding curves for buy and sell prices. 
Putting the Buy Curve b(x) above the Sell Curve s(x) allows 
each transaction to be taxed and the fee is safely withdrawn 
from the contract without the risk of decollateralising the curve.

For eaxmple, an investor is willing to contribute $1000 to a 
new research initiative. With a Tax Rate of 90%, $900 will go 
to a separate funding pool that is used to cover future spending 
while $100 will be locked up in the collateral reserve to provide 
liquidity for token holders that want to burn their stakes by 
sending them back to the bonding curve contract.
"""

# min_slope = 0.1e9
# max_slope = 100e9
# slope_step = 0.1e9

min_slope = 1
max_slope = 100
slope_step = 10

k_min = 0
k_max = 500
k_step = 10

t_min = 0
t_max = 1.0
t_step = 0.01 

# Abstract base class for scenarios with a sigmoid bonding curve
class SigmoidScenario(Scenario):
    def __init__(self, description: str) -> None:
        super().__init__(description)

    def buy_price(self, x, a, b, c, **kwargs):
        raise NotImplementedError
    def sell_price(self, x, a, b, c, **kwargs):
        raise NotImplementedError
    def buy_collateral(self, x, a, b, c, **kwargs):
        raise NotImplementedError
    def sell_collateral(self, x, a, b, c, **kwargs):
        raise NotImplementedError

    
# No tax/fee scenario
# Defined as s0 with no method suffix
class SigmoidNoFeeScenario(Scenario):
    def __init__(self, description: str) -> None:
        super().__init__(description)

    def buy_price(self, x, a, b, c, **kwargs):
        # logger.debug(f'SigmoidNoFeeScenario:buy_price b {b} c {c} x {x}\n{traceback.print_stack(limit=5)}')
        return a * (((x - b) / np.sqrt(c + (x - b)**2)) + 1)
    # Sell price curve equals buy curve in this scenario
    def sell_price(self, x, a, b, c, **kwargs):
        return self.buy_price(x, a, b, c, **kwargs)
    def buy_collateral(self, x, a, b, c, **kwargs):
        return a * (np.sqrt(b**2 - 2 * b * x + c + x**2) + x) - (a*np.sqrt(b**2 + c))
    # No sell curve in this scenario
    def sell_collateral(self, x, a, b, c, **kwargs):
        return np.zeros_like(x)    
        # return self.buy_collateral(x, a, b, c, **kwargs)    

# Constant tax/fee scenario
# Defined as s1 with method suffix _const
class SigmoidConstantFeeScenario(Scenario):
    def __init__(self, description: str) -> None:
        super().__init__(description)

    def buy_price(self, x, a, b, c, **kwargs):
        k = kwargs['k']
        return a * ((x - b) / np.sqrt(c + (x - b)**2) + 1) + k
    def sell_price(self, x, a, b, c, **kwargs):
        return a * ((x - b) / np.sqrt(c + (x - b)**2) + 1)
    def buy_collateral(self, x, a, b, c, **kwargs):
        k = kwargs['k']
        return a * (np.sqrt(b**2 - 2 * b * x + c + x**2) + x) + (k - a*np.sqrt(b**2 + c)) + k*x
    def sell_collateral(self, x, a, b, c, **kwargs):
        return a * (np.sqrt(b**2 - 2 * b * x + c + x**2) + x) - (a*np.sqrt(b**2 + c))    

# Decreasing tax/fee scenario
# Defined as s2 with method suffix _dec
class SigmoidDecreasingFeeScenario(Scenario):
    def __init__(self, description: str) -> None:
        super().__init__(description)

    def buy_price(self, x, a, b, c, **kwargs):
        k = kwargs['k']
        return (a - k/2) * ((x - b) / np.sqrt(c + (x - b)**2) + 1) + k
    def sell_price(self, x, a, b, c, **kwargs):
        return a * ((x - b) / np.sqrt(c + (x - b)**2) + 1)
    def buy_collateral(self, x, a, b, c, **kwargs):
        k = kwargs['k']
        return (a - k/2)*(np.sqrt(b**2 - 2 * b * x + c + x**2) + x) + (k - (a - k/2)*np.sqrt(b**2 + c)) + k*x
    def sell_collateral(self, x, a, b, c, **kwargs):
        return a*(np.sqrt(b**2 - 2 * b * x + c + x**2) + x) - a*np.sqrt(b**2 + c)

# Increasing tax/fee scenario
# Defined as s3 with method suffix _inc
class SigmoidIncreasingFeeScenario(Scenario):
    def __init__(self, description: str) -> None:
        super().__init__(description)

    def buy_price(self, x, a, b, c, **kwargs):
        t = kwargs['t']
        return (a/(1 - t)) * ((x - b) / np.sqrt(c + (x - b)**2) + 1)
    def sell_price(self, x, a, b, c, **kwargs):
        return a * ((x - b) / np.sqrt(c + (x - b)**2) + 1)
    def buy_collateral(self, x, a, b, c, **kwargs):
        t = kwargs['t']
        return (a/(1 - t)) * (np.sqrt((b - x)**2 + c) + x) - (a/(1 - t)) * np.sqrt(b**2 + c)
    def sell_collateral(self, x, a, b, c, **kwargs):
        return a * (np.sqrt(b**2 - 2*b*x + c + x**2) + x) - a*np.sqrt(b**2 + c)

# Gaussian (Bell)-shaped tax/fee scenario
# Defined as s4 with method suffix _bell
class SigmoidGaussianFeeScenario(Scenario):
    def __init__(self, description: str) -> None:
        super().__init__(description)

    def buy_price(self, x, a, b, c, **kwargs):
        return a * ((x - b) / np.sqrt(c + (x - b)**2) + 1)
    def sell_price(self, x, a, b, c, **kwargs):
        h = kwargs['h']
        return a * ((x - h - b) / np.sqrt(c + (x - h - b)**2) + 1)
    def buy_collateral(self, x, a, b, c, **kwargs):
        return a * (np.sqrt(b**2 - 2 * b * x + c + x**2) + x) - a*np.sqrt(b**2 + c)
    def sell_collateral(self, x, a, b, c, **kwargs):
        h = kwargs['h']
        return a * (np.sqrt((b + h - x)**2 + c) + x) - (a*np.sqrt((b + h)**2 + c))

# No constraints tax/fee scenario
# Defined as s5 with method suffix _no
class SigmoidNoConstraintsFeeScenario(Scenario):
    def buy_price(self, x, a, b, c, **kwargs):
        k = kwargs['k']
        return a * ((x - b) / np.sqrt(c + (x - b)**2) + 1) + k
    def sell_price(self, x, a, b, c, **kwargs):
        h = kwargs['h']
        return a * ((x - h - b) / np.sqrt(c + (x - h - b)**2) + 1)
    def buy_collateral(self, x, a, b, c, **kwargs):
        k = kwargs['k']
        return a * (np.sqrt(b**2 - 2 * b * x + c + x**2) + x) + (k - a*np.sqrt(b**2 + c)) + k*x
    def sell_collateral(self, x, a, b, c, **kwargs):
        h = kwargs['h']
        return a * (np.sqrt((b + h - x)**2 + c) + x) - (a*np.sqrt((b + h)**2 + c))
        
# Define a dict of possible scenarios
scenarios = {
    's0': SigmoidNoFeeScenario('No Taxation'),
    's1': SigmoidConstantFeeScenario('Constant Taxation'),
    's2': SigmoidDecreasingFeeScenario('Decreasing Taxation'),
    's3': SigmoidIncreasingFeeScenario('Increasing Taxation'),
    's4': SigmoidGaussianFeeScenario('Bell-Shaped Taxation'),
    's5': SigmoidNoConstraintsFeeScenario('No Constraints')
}


def get_buy_slider_range(scenario_value, a1_max, a1_min, a1_value):
    if scenario_value in scenarios.keys():
        return [
            a1_max,
            a1_min,
            a1_value
        ]
    else:
        return [0, 0, 0]


# update buy inflection point slider ranges based on selected supply
def get_buy_inflection_point_range(supply_value):
    return [supply_value, supply_value/2]


# update sell inflection point ranges based on b1-value
def get_sell_inflection_point_range(scenario_value, b1_max, b1_min, b1_value):
    if scenario_value in scenarios.keys():
        return [
            b1_max,
            b1_min,
            b1_value
            ]

    else:
        return [0, 0, 0]

# update sell slope slider ranges based on buy slope value
def get_sell_slope_ranges(scenario_value, c1_max, c1_min, c1_value):
    if scenario_value in scenarios.keys():
        return [
            c1_max,
            c1_min,
            c1_value
            ]

    else:
        return [0, 0, 0]


# update vertical displacement (buy - sell at t(0)) slider range
def get_vertical_displacement_range(scenario_value, k_max):
    if scenario_value in [None, 's0', 's1', 's2', 's3', 's4']:
        return [k_max/2]
    elif scenario_value == 's5':
        return [0]


# update horizontal displacement slider range
def get_horizontal_displacement_range(scenario_value, b1_max, b1_value, h2_value):
    # inflection point of sell curve needs to lie within supply range
    h2_max = (b1_max - b1_value)

    # only reduce h value if it exceeds new max
    if h2_value > h2_max:
        h2_value = h2_max

    if scenario_value in [None, 's0', 's1', 's2', 's3', 's4']:
        return [h2_max, h2_value]
    elif scenario_value == 's5':
        return [h2_max, 0]


# display curve parameter slider values
def format_slider_outputs(a1_value, b1_value, c1_value, k1_value, t1_value,
                          a2_value, b2_value, c2_value, h2_value):
     return ('Max Token Price: {}'.format(a1_value),
             'Curve Inflection Point: {}'.format(b1_value),
             'Curve Slope: {}'.format(utils.format_number(c1_value)),
             'Buy - Sell t(0): {}'.format(k1_value),
             'Tax Rate: {}'.format(t1_value),
             'Max Token Price: {}'.format(a2_value),
             'Curve Inflection Point: {}'.format(b2_value),
             'Curve Slope: {}'.format(utils.format_number(c2_value)),
             'Horizontal Displacement: {}'.format(h2_value))


class Sigmoid(BondingCurve):
    curve_parameters = None

    def __init__(self, min_supply:int, supply:int, price:float) -> None:
        BondingCurve.__init__(self, supply, supply, price)
        self.curve_parameters = {
            'scenario': 's0',
            'supply': supply,
            'buy_price': price,
            'buy_supply': supply / 2,
            'buy_slope': max_slope / 10,
            'vertical_displacement': k_max/2,
            'tax': t_max/5,
            'sell_price': price,
            'sell_supply': supply / 2,
            'sell_slope': max_slope / 10,
            'horizontal_displacement': supply / 5,
        }


    def token_dynamics(self, supply:List, curve_parameters:Dict=None) -> pd.DataFrame:
        if curve_parameters is None:
            curve_parameters = self.curve_parameters
        
        logger.info(f'curve_parameters {curve_parameters}')

        scenario_value = curve_parameters['scenario']
        kwargs = {
            'k': curve_parameters['vertical_displacement'] ,
            'h': curve_parameters['horizontal_displacement'],
            't': curve_parameters['tax']
        }

        if scenario_value is None:
            return None
        else:
            scenario = scenarios[scenario_value]
        logger.debug(f'Scenario: {scenario.description}')

        #
        # The Price Function p(x) returns the price for a single token 
        # at a specific supply while the Collateral Function C(x) returns 
        # the total capital needed to mint or burn a specified amount of tokens.
        #

        d = {'supply': supply,
             'buy_price': scenario.buy_price(supply, 
                                             curve_parameters['buy_price'], 
                                             curve_parameters['buy_supply'], 
                                             curve_parameters['buy_slope'], 
                                             **kwargs),
             'sell_price': scenario.sell_price(supply, 
                                               curve_parameters['sell_price'], 
                                               curve_parameters['sell_supply'], 
                                               curve_parameters['sell_slope'], 
                                               **kwargs),
             'buy_col': scenario.buy_collateral(supply, 
                                                curve_parameters['buy_price'], 
                                                curve_parameters['buy_supply'], 
                                                curve_parameters['buy_slope'], 
                                                **kwargs),
             'sell_col': scenario.sell_collateral(supply, 
                                                  curve_parameters['sell_price'], 
                                                  curve_parameters['sell_supply'], 
                                                  curve_parameters['sell_slope'], 
                                                  **kwargs)}

        df = pd.DataFrame(data=d)

        # compute tax and fund metrics
        # Tax Rate relates the amount going to the funding pool and 
        # the actual buy price at a specific supply
        df['tax_rate'] = np.around(1 - df['sell_price']/df['buy_price'], decimals=4)
        df['tax_amount'] = np.around(df['buy_price'] - df['sell_price'], decimals=4)
        df['fund_rate'] = np.around(1 - df['sell_col']/df['buy_col'], decimals=4)
        df['fund_amount'] = np.around(df['buy_col'] - df['sell_col'], decimals=4)

        # Formatted text for hover labels
        df['buy_col_text'] = df['buy_col'].apply(utils.format_number)
        df['sell_col_text'] = df['sell_col'].apply(utils.format_number)
        df['fund_rate_text'] = np.around(df['fund_rate'], decimals=2).map('{:.2f}'.format)
        df['fund_amount_text'] = df['fund_amount'].apply(utils.format_number)

        return df