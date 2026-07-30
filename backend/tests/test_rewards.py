"""Unit tests for Reward domain models and check constraints (D-02)."""

from typing import cast

from sqlalchemy import Table

from backend.models.citizens import Citizen
from backend.models.rewards import RewardTransaction


def test_reward_transaction_check_constraints():
    """Verify RewardTransaction table has database-level CheckConstraints (D-02)."""
    table = cast(Table, RewardTransaction.__table__)
    constraint_names = {c.name for c in table.constraints if c.name}

    assert "chk_reward_tx_balance_calc" in constraint_names
    assert "chk_reward_tx_new_balance_non_negative" in constraint_names
    assert "chk_reward_tx_prev_balance_non_negative" in constraint_names


def test_citizen_points_check_constraint():
    """Verify Citizen table has non-negative points CheckConstraint (D-02)."""
    table = cast(Table, Citizen.__table__)
    constraint_names = {c.name for c in table.constraints if c.name}

    assert "chk_citizen_points_non_negative" in constraint_names
