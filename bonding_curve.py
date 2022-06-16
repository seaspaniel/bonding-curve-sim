from typing import List
import pandas as pd

class BondingCurve:
    min_supply = 10000
    max_supply = 1000000
    supply_step = 1000

    min_price = 0
    max_price = 1000
    price_step = 10

    # When using buy and sell curves, this is the 
    # vertical displacement: Buy - Sell t(0)
    k_min = 0
    k_max = 500
    k_step = 10

    # Tax Rate
    t_min = 0
    t_max = 1.0
    t_step = 0.01 

    def __init__(self, min_supply:int, max_supply:int, max_price:float) -> None:
        self.min_supply = min_supply
        self.max_supply = max_supply
        self.max_price = max_price


    def token_dynamics(self, supply:List, **kwargs:int) -> pd.DataFrame:
        raise NotImplementedError