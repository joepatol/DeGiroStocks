from __future__ import annotations

from dataclasses import dataclass
from typing import List, Dict

import pandas as pd

from .product import Product


@dataclass
class Portfolio:
    """A DeGiro portfolio for a given account and session"""
    items: List[Product]
    unused_amount: float

    @property
    def value(self) -> float:
        return sum([item.value for item in self.items])

    @property
    def portfolio_shares(self) -> Dict[str, float]:
        return {item.id_nr: item.value / self.value for item in self.items}

    def to_dataframe(self) -> pd.DataFrame:
        df = pd.DataFrame.from_records(
            data=[product.to_dict() for product in self.items],
            index=[i for i in range(len(self.items))]
        ).rename(columns={"_quantity": "quantity"})

        df['share'] = df['id_nr'].map(self.portfolio_shares)

        return df
