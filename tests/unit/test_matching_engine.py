import pytest
import time
from apps.mock_exchange.src.engine import MatchingEngine, Order, OrderSide

class TestMatchingEngine:
    @pytest.fixture
    def engine(self):
        return MatchingEngine()

    def test_place_order_no_match(self, engine):
        """
        Scenario: Placing a BUY order in an empty book.
        Result: No trades, order added to bids.
        """
        order = Order(
            id="1", symbol="AAPL", qty=10, side=OrderSide.BUY, limit_price=100.0
        )
        trades = engine.place_order(order)
        
        assert len(trades) == 0
        assert len(engine.bids["AAPL"]) == 1
        assert engine.bids["AAPL"][0].qty == 10

    def test_match_buy_sell(self, engine):
        """
        Scenario: 
        1. Sell 10 @ 100
        2. Buy 10 @ 100
        Result: 1 Trade, Book empty.
        """
        # 1. Place Sell
        sell_order = Order(id="s1", symbol="AAPL", qty=10, side=OrderSide.SELL, limit_price=100.0)
        engine.place_order(sell_order)
        
        # 2. Place Buy
        buy_order = Order(id="b1", symbol="AAPL", qty=10, side=OrderSide.BUY, limit_price=100.0)
        trades = engine.place_order(buy_order)
        
        assert len(trades) == 1
        assert trades[0].price == 100.0
        assert trades[0].qty == 10
        assert len(engine.asks["AAPL"]) == 0 # Filled
        assert "AAPL" not in engine.bids or len(engine.bids["AAPL"]) == 0

    def test_partial_fill(self, engine):
        """
        Scenario:
        1. Sell 10 @ 100
        2. Buy 5 @ 100
        Result: 1 Trade (5), Sell order remains with qty 5.
        """
        engine.place_order(Order(id="s1", symbol="AAPL", qty=10, side=OrderSide.SELL, limit_price=100.0))
        
        trades = engine.place_order(Order(id="b1", symbol="AAPL", qty=5, side=OrderSide.BUY, limit_price=100.0))
        
        assert len(trades) == 1
        assert trades[0].qty == 5
        assert engine.asks["AAPL"][0].qty == 5
