from stockrhythm.models import Order

def validate_order(order: Order, account_state: dict) -> bool:
    # Rule 1: Buying Power Check
    cost = order.qty * (order.limit_price if order.limit_price else 0) # simplified for market order
    if cost > account_state['cash']:
        return False
    
    # Rule 2: Max Order Size
    if order.qty > 1000:
        return False
        
    return True
