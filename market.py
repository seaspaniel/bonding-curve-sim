from typing import Dict

import numpy as np
import pandas as pd

import logging

from bonding_curve import BondingCurve

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

# initial conditions
min_supply = 100  # 10000
max_supply = 2000  # 1000000
initial_supply = max_supply/2
supply_value = max_supply/2
supply_step = min_supply * .1  #  1000

min_price = 0
max_price = 100  # 1000
price_step = 10

class Market:
    # Some funds go to a reserve (based on tax rates) and the rest go
    # to an operating fund
    # Reserve funds from taxation
    collateral_balance = 0.0
    # Operating funds from purchases
    fund_balance = 0.0
    tokens_circulation = 0
    tokens_bought = 0
    tokens_sold = 0
    supply = supply_value

    bonding_curve = None
    token_dynamics = None

    def __init__(self, bonding_curve:BondingCurve) -> None:
        self.bonding_curve = bonding_curve
        self.token_dynamics = self.update_token_dynamics(self.supply)
        # logger.info(f'token_dynamics init {self.token_dynamics}')


    def reset(self):
        self.collateral_balance = 0.0
        self.fund_balance = 0.0
        self.tokens_circulation = 0
        self.tokens_bought = 0
        self.tokens_sold = 0       


    def update_token_dynamics(self, supply:int, curve_parameters:Dict=None) -> pd.DataFrame:
        # if len(curve_parameters > 0):
        #     self.bonding_curve.update_parameters(curve_parameters)
        self.supply = supply
        s = np.arange(0., supply + 1)  #  , supply/n_points)
        self.token_dynamics = self.bonding_curve.token_dynamics(s, curve_parameters)
        # logger.info(f'token_dynamics update {self.token_dynamics}')
        return self.token_dynamics


    # Buy tokens (swap in)
    def buy_tokens(self, num_tokens: float):
        """Swap reserve currency for tokens.

        Parameters
        ----------
        number_of_tokens: float
            The number of tokens purchased
            
        Returns
        -------
        amount: float
            The amount of reserve currency swapped in exchange for tokens.
        tax_amount: float
            The transaction fee.
        """
        if self.token_dynamics is None:
            logger.info(f'buy_tokens token_dynamics {self.token_dynamics}')
            raise RuntimeError("Bonding curve is not initialized.  Cannot execute transaction.")
        # logger.info(f'buy_tokens token_dynamics cols {self.token_dynamics.columns}')
        start = self.tokens_circulation
        end = min(start + num_tokens, len(self.token_dynamics) - 1)
        num_tokens = end - start
        # logger.info(f'buy_tokens start {start} end {end} token_dynamics len {len(self.token_dynamics)}')

        p = self.token_dynamics[['buy_price', 'tax_amount', 'fund_amount']][start:end]
        # logger.debug(f'buy_tokens token_dynamics[{start}:{end}]\n{p}')
        p = p.agg({'buy_price': 'sum',
                   'tax_amount': 'sum',
                   'fund_amount': 'sum'
        })
    
        # logger.info(f'buy_tokens p agg {p}')
        amount = p['buy_price']  # the sum of prices in the slice
        tax_amount = p['tax_amount']
        net_asset_value = amount - tax_amount
        self.collateral_balance += net_asset_value
        self.fund_balance += tax_amount  
        self.tokens_bought = num_tokens
        self.tokens_circulation += num_tokens
        self.tokens_circulation = min(self.tokens_circulation, self.supply)
        return num_tokens, amount, tax_amount


    # To be implemented
    def buy_amount(self, amount: float):
        """Swap reserve currency for tokens.

        Parameters
        ----------
        amount: float
            The amount of reserve currency to swap in exchange for tokens.

        Returns
        -------
        num_tokens: float
            The number of tokens purchased
        fee: float
            The transaction fee.
        """
        if self.token_dynamics is None:
            raise RuntimeError("Bonding curve is not initialized.  Cannot execute transaction.")
        raise NotImplementedError


    # Sell tokens (swap out)
    def sell_tokens(self, num_tokens: float):
        """Swap tokens for reserve currency.

        Parameters
        ----------
        num_tokens: float
            The number of tokens to swap in exchange for reserve currency.

        Returns
        -------
        amount: float
            The amount of reserve currency
        fee: float
            The transaction fee.
        """
        if self.token_dynamics is None:
            raise RuntimeError("Bonding curve is not initialized.  Cannot execute transaction.")
        start = self.tokens_circulation
        end = min(start + num_tokens, len(self.token_dynamics) - 1)
        num_tokens = end - start
        p = self.token_dynamics[['sell_price', 'tax_amount', 'fund_amount']][start:end]
        p = p.agg({'sell_price': 'sum',
                   'tax_amount': 'sum',
                   'fund_amount': 'sum'
        })
        amount = p['sell_price']
        tax_amount = p['tax_amount']
        self.collateral_balance -= amount
        # self.fund_balance -= tax_amount
        self.tokens_sold = num_tokens
        self.tokens_circulation -= num_tokens
        return num_tokens, amount, tax_amount


    # To be implemented
    def sell_amount(self, amount: float):
        """Swap tokens for reserve currency.

        Parameters
        ----------
        amount: float
            The value of tokens to swap in exchange for reserve currency.

        Returns
        -------
        num_tokens: float
            The number of tokens swapped
        fee: float
            The transaction fee.
        """
        if self.token_dynamics is None:
            raise RuntimeError("Bonding curve is not initialized.  Cannot execute transaction.")
        raise NotImplementedError

        
    def buy_price(self):
        if self.token_dynamics is None:
            raise RuntimeError("Bonding curve is not initialized.  Cannot get pricing.")
        try:
            price = self.token_dynamics[['buy_price']].iloc[self.tokens_circulation].sum()
            return price
        except IndexError as e:
            logger.info('Error in buy_price {}:{}'.format(self.tokens_circulation, len(self.token_dynamics[['buy_price']])))  


    def sell_price(self):
        if self.token_dynamics is None:
            raise RuntimeError("Bonding curve is not initialized.  Cannot get pricing.")
        return self.token_dynamics[['sell_price']].iloc[self.tokens_circulation].sum()
