from dataclasses import dataclass


@dataclass(frozen=True)
class Action:
    """Action to be performed"""
    id_nr: str
    amount: int
    limit: float

    def print(self) -> None:
        print(f"Buy {self.amount} of {self.id_nr}. Max price: {self.limit}")
