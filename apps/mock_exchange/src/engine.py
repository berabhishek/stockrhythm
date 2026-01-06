from pydantic import BaseModel
from typing import List, Optional
import time
from enum import Enum

class OrderSide(str, Enum):
    BUY = "BUY"
    SELL = "SELL"

class Order(BaseModel):
    id: str
    symbol: str
    qty: int
    side: OrderSide
    limit_price: float
    timestamp: float = 0.0

class Trade(BaseModel):
    symbol: str
    qty: int
    price: float
    timestamp: float
    buy_order_id: str
    sell_order_id: str

class MatchingEngine:
    def __init__(self):
        # symbol -> list[Order] (sorted by price/time)
        self.bids = {} 
        self.asks = {}
        self.trades = []

    def place_order(self, order: Order) -> List[Trade]:
        order.timestamp = time.time()
        if order.symbol not in self.bids:
            self.bids[order.symbol] = []
            self.asks[order.symbol] = []

        trades = []
        
        if order.side == OrderSide.BUY:
            trades = self._match_buy(order)
        else:
            trades = self._match_sell(order)
            
        self.trades.extend(trades)
        return trades

    def _match_buy(self, order: Order) -> List[Trade]:
        trades = []
        asks = self.asks[order.symbol]
        
        # Match against asks (lowest price first)
        # Note: In a real LOB, asks are sorted ascending
        asks.sort(key=lambda x: (x.limit_price, x.timestamp))
        
        remaining_qty = order.qty
        
        while remaining_qty > 0 and asks:
            best_ask = asks[0]
            if best_ask.limit_price > order.limit_price:
                break # No match possible
                
            trade_qty = min(remaining_qty, best_ask.qty)
            price = best_ask.limit_price # Maker's price
            
            trades.append(Trade(
                symbol=order.symbol,
                qty=trade_qty,
                price=price,
                timestamp=time.time(),
                buy_order_id=order.id,
                sell_order_id=best_ask.id
            ))
            
            remaining_qty -= trade_qty
            best_ask.qty -= trade_qty
            
            if best_ask.qty == 0:
                asks.pop(0)
                
        if remaining_qty > 0:
            order.qty = remaining_qty
            self.bids[order.symbol].append(order)
            
        return trades

    def _match_sell(self, order: Order) -> List[Trade]:
        trades = []
        bids = self.bids[order.symbol]
        
        # Match against bids (highest price first)
        bids.sort(key=lambda x: (-x.limit_price, x.timestamp))
        
        remaining_qty = order.qty
        
        while remaining_qty > 0 and bids:
            best_bid = bids[0]
            if best_bid.limit_price < order.limit_price:
                break
                
            trade_qty = min(remaining_qty, best_bid.qty)
            price = best_bid.limit_price
            
            trades.append(Trade(
                symbol=order.symbol,
                qty=trade_qty,
                price=price,
                timestamp=time.time(),
                buy_order_id=best_bid.id,
                sell_order_id=order.id
            ))
            
            remaining_qty -= trade_qty
            best_bid.qty -= trade_qty
            
            if best_bid.qty == 0:
                bids.pop(0)
        
        if remaining_qty > 0:
            order.qty = remaining_qty
            self.asks[order.symbol].append(order)
            
        return trades
