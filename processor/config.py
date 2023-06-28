from __future__ import annotations

import json
from dataclasses import dataclass
from typing import Dict, Any
from enum import Enum


class Strategy(Enum):
    """Definition of possible action strategies"""
    BUY = "buy"
    SELL = "sell"
    BUY_AND_SELL = "buy_and_sell"


@dataclass
class Config:
    """Configuration for the processor that determines the action(s)"""
    target_shares: Dict[str, float]
    strategy: Strategy
    to_email: str

    @classmethod
    def from_dict(cls, input_dict: Dict[str, Any]) -> Config:
        targets = input_dict["target_shares"]

        for k, v in targets.items():
            targets[k] = float(v)

        if round(sum(targets.values()), 5) != 1:
            raise ValueError("Sum of target shares is not 1")

        return cls(
            target_shares=input_dict["target_shares"],
            to_email=input_dict["to_email"],
            strategy=Strategy(input_dict["strategy"]),
        )

    @classmethod
    def from_json_file(cls, file_path: str) -> Config:
        with open(file_path, "r") as file:
            content = file.read()
        return cls.from_json(content)

    @classmethod
    def from_json(cls, input_json: str) -> Config:
        return cls.from_dict(json.loads(input_json))
