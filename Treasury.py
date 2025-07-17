from Order import Order
from Outgoings import Outgoings
from datetime import datetime

class Treasury():
    def __init__(self, total_balance=0, date=None):
        self.total_balance = total_balance
        self.date = date or datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    def add_outgoing(self, outgoing):
        if not isinstance(outgoing, Outgoings):
            raise ValueError("Invalid outgoing type.")
        outgoings = Outgoings.load_all()
        outgoings.append(outgoing)
        Outgoings.save_all(outgoings)


    def remove_outgoing(self, outgoing):
        if not isinstance(outgoing, Outgoings):
            raise ValueError("Invalid outgoing type.")
        outgoings = Outgoings.load_all()
        outgoings = [o for o in outgoings if o.id != outgoing.id]
        Outgoings.save_all(outgoings)
    
    def add_order(self, order):
        if not isinstance(order, Order):
            raise ValueError("Invalid order type.")
        orders = Order.load_orders_from_json()
        orders.append(order)
        Order.save_orders_to_json(orders)

    def remove_order(self, order):
        if not isinstance(order, Order):
            raise ValueError("Invalid order type.")
        orders = Order.load_orders_from_json()
        orders = [o for o in orders if o.id != order.id]
        Order.save_orders_to_json(orders)