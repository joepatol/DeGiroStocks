from typing import List, Dict
from dataclasses import dataclass

import numpy as np

from .action import Action


STEP_LIMIT_MULTIPLIER = 1.05


@dataclass(frozen=True)
class MinimizeResult:
    ids: List[str]
    initial_shares: List[float]
    new_shares: List[float]
    steps: np.ndarray[int]
    remaining_amount: float
    limits: List[float]

    def get_actions(self) -> List[Action]:
        return [
            Action(self.ids[i], self.steps[i], self.limits[i])
            for i in range(len(self.ids)) if self.steps[i] != 0
        ]

    def to_dict(self) -> Dict[str, int]:
        return {self.ids[i]: self.steps[i] for i in range(len(self.ids)) if self.steps[i] != 0}

    def to_string(self, human_readables: Dict[str, str]) -> str:
        d = {human_readables[k]: v for k, v in self.to_dict().items()}
        return "\n        ".join([f"- {amount} {name}" for name, amount in d.items()])


def minimize_distance_to_targets(
        ids: np.array,
        targets: np.array,
        values: np.array,
        steps: np.array,
        additional_space: float,
) -> MinimizeResult:
    limits = steps * STEP_LIMIT_MULTIPLIER

    initial_shares = values / sum(values)

    space_left = additional_space
    to_step = np.zeros(ids.shape)

    while space_left > np.min(steps) * STEP_LIMIT_MULTIPLIER:

        # Calculate current status
        total = sum(values)
        current_shares = values / total
        current_distances = np.abs(targets - current_shares)

        # Check which steps we can do
        can_step = np.array(
            [is_step_allowed(steps[i], space_left) for i in range(len(ids))]
        )

        # If we can't do anything, break
        if sum(can_step) == 0:
            break

        # Join the step sizes and if we can do them
        steps = np.where(can_step == False, 0, steps)

        # Calculate potential new shares
        shares_after_step = np.array(
            [calculate_share_after_step(values[i], steps[i], total) for i in range(len(ids))]
        )

        # Calculate the new distance
        distances_after_step = np.abs(targets - shares_after_step)

        # Get the max of the distances
        distances_diff = current_distances - distances_after_step
        picked = np.argmax(distances_diff)

        # If < 0 is picked, we can only increase our distribution
        if distances_diff[picked] <= 0:
            picked = pick_random(can_step)

        # Set the new values
        values[picked] = values[picked] + steps[picked]
        to_step[picked] += 1

        space_left = space_left - steps[picked]

    new_shares = values / sum(values)

    return MinimizeResult(
        ids=ids,
        initial_shares=initial_shares,
        new_shares=new_shares,
        remaining_amount=space_left,
        steps=to_step.astype(int),
        limits=limits,
    )


def pick_random(can_step: np.array) -> float:
    return np.random.choice(np.where(can_step == True)[0], size=1)[0]


def calculate_share_after_step(current_share: float, step: float, total: float) -> float:
    return (current_share + step) / total


def is_step_allowed(step: float, limit: float) -> bool:
    return step * STEP_LIMIT_MULTIPLIER <= limit and step != 0
