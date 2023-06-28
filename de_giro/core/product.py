from __future__ import annotations

from dataclasses import dataclass, asdict
from typing import Dict, Any, ClassVar


@dataclass
class Product:
    """
    A De Giro product
    """
    product_type: ClassVar[str]

    id_nr: str
    name: str
    isin: str
    symbol: str
    price: float
    currency: str
    _quantity: int = 0

    @property
    def quantity(self) -> int:
        return self._quantity

    @quantity.setter
    def quantity(self, quantity: int) -> None:
        self._quantity = quantity

    @property
    def value(self) -> float:
        return self.quantity * self.price

    @classmethod
    def from_dict(cls, input_dict: Dict[str, Any]) -> Product:
        subclasses = {klass.product_type: klass for klass in cls.__subclasses__()}

        product_type = input_dict["productType"]

        try:
            klass = subclasses[product_type]
        except KeyError:
            raise NotImplementedError(f"Product type {product_type} not implemented")

        # Price is live or the closing price
        price = input_dict.get("price")
        if not price:
            price = input_dict["closePrice"]

        return klass(
            id_nr=input_dict["id"],
            name=input_dict["name"],
            isin=input_dict["isin"],
            symbol=input_dict["symbol"],
            price=price,
            currency=input_dict["currency"]
        )

    def to_dict(self) -> Dict[str, Any]:
        d = asdict(self)
        d["quantity"] = d.pop("_quantity")
        d["value"] = self.value
        return d


class ETF(Product):
    """An ETF product"""
    product_type: ClassVar[str] = "ETF"
