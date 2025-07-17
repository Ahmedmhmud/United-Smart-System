import uuid
from datetime import datetime
from Product import Product
import json
import os
import sys

def resource_path(relative_path):
    """Get path to resource for PyInstaller or normal run"""
    base_path = getattr(sys, '_MEIPASS', os.path.abspath("."))
    return os.path.join(base_path, relative_path)

class Order():
    def __init__(self, client_id, products, total_price, cash_paid_now=0, id=None, date=None):
        self.id = id or uuid.uuid4().hex[:8]
        self.client_id = client_id
        self.products = products
        self.total_price = total_price
        self.cash_paid_now = cash_paid_now
        self.date = date or datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    def add_product(self, product, final_price, wanted_quantity):
        if final_price < product.price:
            raise ValueError("Final price cannot be less than product price.")
        if wanted_quantity > product.quantity:
            raise ValueError("Wanted quantity exceeds available stock.")
    
        self.products.append((product, wanted_quantity, final_price))
        self.total_price += final_price * wanted_quantity
        product.quantity -= wanted_quantity

    def remove_product(self, product, final_price, wanted_quantity):
        for i, (p, q, f) in enumerate(self.products):
            if p.id == product.id and q == wanted_quantity and f == final_price:
                self.products.pop(i)
                self.total_price -= final_price * wanted_quantity
                product.quantity += wanted_quantity
                return
        raise ValueError("Product not found in order.")
    
    def to_dict(self):
        return {
            "id": self.id,
            "client_id": self.client_id,
            "products": [
                {
                    "product": product.to_dict(),
                    "quantity": quantity,
                    "final_price": final_price
                } for product, quantity, final_price in self.products
            ],
            "total_price": self.total_price,
            "cash_paid_now": self.cash_paid_now,
            "date": self.date
        }
    
    @classmethod
    def from_dict(cls, data):
        products = []
        for item in data["products"]:
            product = Product.from_dict(item["product"])
            quantity = item["quantity"]
            final_price = item["final_price"]
            products.append((product, quantity, final_price))

        return cls(
            client_id=data["client_id"],
            products=products,
            total_price=data["total_price"],
            cash_paid_now=data["cash_paid_now"],
            id=data["id"],
            date=data["date"]
        )
    
    
    @staticmethod
    def save_orders_to_json(orders, file_path=resource_path("data/orders.json")):
        with open(file_path, "w", encoding="utf-8") as f:
            data = [order.to_dict() for order in orders]
            json.dump(data, f, ensure_ascii=False, indent=4)

    @staticmethod
    def load_orders_from_json(file_path=resource_path("data/orders.json"), from_date=None, to_date=None):
        from datetime import datetime
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                orders_data = json.load(f)
                orders = []
                for data in orders_data:
                    products = []
                    for item in data["products"]:
                        product = Product.from_dict(item["product"])
                        quantity = item["quantity"]
                        final_price = item["final_price"]
                        products.append((product, quantity, final_price))
                    order = Order(
                        client_id=data["client_id"],
                        products=products,
                        total_price=data["total_price"],
                        cash_paid_now=data.get("cash_paid_now", 0),
                        id=data["id"],
                        date=data["date"]
                    )
                    # === Filter by date ===
                    if from_date or to_date:
                        order_date = datetime.strptime(order.date, "%Y-%m-%d %H:%M:%S").date()
                        from_date = from_date or datetime.now().date()
                        to_date = to_date or datetime.now().date()
                        if not (from_date <= order_date <= to_date):
                            continue
                    orders.append(order)
                return orders
        except FileNotFoundError:
            return []
        except Exception as e:
            print("Error while loading orders:", e)
            return []
