"""Implements user actions."""

from typing import Tuple

import numpy as np
import random

import logging

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

class TokenUser:
    tokens = 0
    capital = 100000
    transaction_history = []

    initial_tokens = tokens
    initial_capital = capital

    policy = 'Buy'
    # policy = 'Alternate'

    def __init__(self, tokens:float, capital:float) -> None:
        self.tokens = tokens
        self.initial_tokens = tokens
        self.capital = capital
        self.initial_capital = capital


    def reset(self):
        self.tokens = self.initial_tokens
        self.capital = self.initial_capital
        self.transaction_history = []


    def get_transaction(self, price: float) -> Tuple[str, float]:
        """Get the transaction the agent wants to execute.

        Parameters
        ----------
        price: float
            The price of the token.

        Returns
        -------
        action: str
            The Buy or Sell action the agent is taking.
        value: float
            The number of tokens to buy or sell.
        """
        number_of_tokens = 1  # int(random.uniform(1, 10))
        cost = price * number_of_tokens
        logger.debug(f'price {price} tokens {number_of_tokens} cost {cost} capital {self.capital}')
        if self.policy == 'Buy':
            if cost <= self.capital:
                return 'Buy', number_of_tokens
            else: 
                return 'Sell', number_of_tokens
        elif self.policy == 'Alternate':
            if len(self.transaction_history) < 1 and cost <= self.capital:
                return 'Buy', number_of_tokens
            else: 
                last_action = self.transaction_history[-1]['action']
                if last_action == 'Buy':
                    action = 'Sell'
                elif last_action == 'Sell':
                    action = 'Buy'
                return action, number_of_tokens


    def transaction_update(self, action: str, tokens: float, amount: float, fee: float) -> Tuple[float, float]:
        """Update the agent with the results of a transaction.

        Parameters
        ----------
        tokens: float
            The number of tokens in the transaction.
        amount: float
            The amount of capital used in the transaction.
        fee: float
            The fee charged for the transaction.

        Returns
        -------
        capital: float
            The amount of capital the agent has after the transaction.
        value: float
            The number of tokens the agent has after the transaction.
        """
        self.transaction_history.append(
            {
                'action': action,
                'tokens': tokens,
                'amount': amount,
                'fee': fee
            }
        )
        
        if action == 'Buy':
            self.capital += -amount - fee
            self.tokens += tokens
        elif action == 'Sell':
            self.capital += amount - fee
            self.tokens -= tokens
        self.capital = max(0, self.capital)
        logger.debug(f'update_capital amount {amount} fee {fee} remaining capital {self.capital}')
        return self.capital, self.tokens


