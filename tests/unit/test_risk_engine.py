import pytest
from stockrhythm.models import Order, OrderSide, OrderType
from apps.backend.src.risk_engine import validate_order

class TestRiskEngine:
    @pytest.fixture
    def account_state(self):
        return {"cash": 10000.0}

    def test_validate_order_success(self, account_state):
        """
        Scenario: User has enough cash and order size is within limits.
        """
        order = Order(
            symbol="AAPL",
            qty=10,
            side=OrderSide.BUY,
            type=OrderType.LIMIT,
            limit_price=150.0
        )
        assert validate_order(order, account_state) is True

    def test_validate_order_insufficient_funds(self, account_state):
        """
        Scenario: Order cost exceeds cash balance.
        """
        order = Order(
            symbol="AAPL",
            qty=100,
            side=OrderSide.BUY,
            type=OrderType.LIMIT,
            limit_price=150.0 # Cost: 15,000 > 10,000
        )
        assert validate_order(order, account_state) is False

    def test_validate_order_qty_too_large(self, account_state):
        """
        Scenario: Quantity exceeds the hard guardrail (1000).
        """
        order = Order(
            symbol="PENNY",
            qty=2000,
            side=OrderSide.BUY,
            type=OrderType.LIMIT,
            limit_price=1.0 # Cost: 2000 < 10,000 (Affordable but illegal size)
        )
        assert validate_order(order, account_state) is False
