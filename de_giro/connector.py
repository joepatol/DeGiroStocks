from __future__ import annotations

from typing import List, Optional, Any
import datetime
from dateutil.relativedelta import relativedelta
import json
from dataclasses import dataclass

import requests

from . import urls
from .core.portfolio import Portfolio
from .core.product import Product
from .core.order import Order

ANTI_BOT_HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_10_1) '
                  'AppleWebKit/537.36 (KHTML, like Gecko) Chrome/39.0.2171.95 Safari/537.36'
}


def get(*args: Any, headers=None, **kwargs: Any) -> requests.Response:
    """Wrapper around requests.get so we can modify the behavior if needed"""
    headers = ANTI_BOT_HEADERS if not headers else {**headers, **ANTI_BOT_HEADERS}
    return requests.get(*args, headers=headers, **kwargs)


def post(*args: Any, headers=None, **kwargs: Any) -> requests.Response:
    """Wrapper around requests.post so we can modify the behavior if needed"""
    headers = ANTI_BOT_HEADERS if not headers else {**headers, **ANTI_BOT_HEADERS}
    return requests.post(*args, headers=headers, **kwargs)


@dataclass
class DeGiroConnector:
    """Connect to DeGiro with username and password"""
    _session_id: str
    _account_id: str

    @property
    def session_id(self) -> str:
        return self._session_id

    @property
    def account_id(self) -> str:
        return self._account_id

    @classmethod
    def login(cls, username: str, password: str) -> DeGiroConnector:
        payload = {
            'username': username,
            'password': password,
            'isPassCodeReset': False,
            'isRedirectToMobile': False
        }

        session_id = post(
                urls.LOGIN,
                json=payload,
            ).json()['sessionId']

        account_id = get(
                urls.CLIENT_INFO,
                params={"sessionId": session_id},
            ).json()['data']['intAccount']

        return cls(
            _session_id=session_id,
            _account_id=account_id
        )

    def logout(self) -> None:
        payload = {
            "intAccount": self.account_id,
            "sessionId": self.session_id,
        }

        get(f"{urls.LOGOUT};jsessionid={self.session_id}", params=payload)

    def get_portfolio(self) -> Portfolio:
        """Get the De Giro portfolio"""
        payload = {
            'portfolio': 0,
            'intAccount': self.account_id,
            'sessionId': self.session_id
        }

        raw_data = get(f"{urls.DATA}/{self.account_id};jsessionid={self.session_id}", params=payload).json()

        portfolio_entries = []

        for row in raw_data['portfolio']['value']:
            entry = dict()
            for y in row['value']:
                k = y['name']
                v = None
                if 'value' in y:
                    v = y['value']
                entry[k] = v
            # Also historic equities are returned, let's omit them
            if entry['size'] != 0:
                portfolio_entries.append(entry)

        portfolio_items = {entry["id"]: entry["size"] for entry in portfolio_entries}

        # Get the cash amount we have
        unused_amount = portfolio_items.pop("FLATEX_EUR", 0) + portfolio_items.pop("EUR", 0)

        # Drop dollars as we could have them through dividend, they can't be used directly anyway
        portfolio_items.pop("USD", None)

        products = self.get_products_by_id(list(portfolio_items.keys()))

        for p in products:
            p.quantity = portfolio_items[p.id_nr]

        return Portfolio(items=products, unused_amount=unused_amount)

    def search_products(self, search_text: str, limit: int = 10) -> List[Product]:
        """Search De Giro products by a search text."""
        product_search_payload = {
            'searchText': search_text,
            'limit': limit,
            'offset': 0,
            'intAccount': self.account_id,
            'sessionId': self.session_id
        }

        raw_data = get(urls.SEARCH_PRODUCTS, params=product_search_payload).json()['products']
        return [Product.from_dict(product_data) for product_data in raw_data]

    def get_products_by_id(self, product_ids: List[str]) -> List[Product]:
        """Return Product objects from a list of product ids"""
        header = {'content-type': 'application/json'}
        raw_data = post(
            urls.PRODUCT_INFO,
            headers=header,
            params={
                'intAccount': self.account_id,
                'sessionId': self.session_id,
            },
            data=json.dumps(product_ids)
        ).json()['data']

        return [Product.from_dict(product_data) for product_data in raw_data.values()]

    def buy_order(self, product_id: str, amount: int, limit: float) -> None:
        """Buy a number of shares of a product."""
        params = {
            'intAccount': self.account_id,
            'sessionId': self.session_id,
        }
        payload = {
            'buySell': "BUY",
            'orderType': 0,  # limit order
            'productId': str(product_id),
            'timeType': 1,
            'size': int(amount),
            'price': float(limit),
            'stopPrice': None,
        }

        header = {'content-type': 'application/json'}

        confirmation_id = post(
            f"{urls.PLACE_ORDER};jsessionid={self.session_id}",
            data=json.dumps(payload),
            params=params,
            headers=header,
        ).json()['data']['confirmationId']

        post(
            f"{urls.ORDER}/{confirmation_id};jsessionid={self.session_id}",
            data=json.dumps(payload),
            params=params,
            headers=header,
        )

    def sell_order(self, product_id: str, amount: int, limit: float) -> None:
        raise NotImplementedError()

    def get_open_orders(self, from_date: Optional[datetime] = None, days: int = 7) -> List[Order]:
        """Get the open orders of the last days."""
        # TODO: analyze what order contains so I can create a dataclass that represents it
        from_date = datetime.datetime.today() if from_date is None else from_date

        orders_payload = {
            'fromDate': from_date.strftime("%d/%m/%Y"),
            'toDate': (from_date - relativedelta(days=days)).strftime("%d/%m/%Y"),
            'intAccount': self.account_id,
            'sessionId': self.session_id
        }

        data = get(urls.LIST_ORDERS, params=orders_payload).json()['data']

        return [d for d in data if d['isActive']]
