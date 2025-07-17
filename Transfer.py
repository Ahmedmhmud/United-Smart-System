import uuid
from datetime import datetime
import csv
import os
import sys

def resource_path(relative_path):
    """Get path to resource for PyInstaller or normal run"""
    base_path = getattr(sys, '_MEIPASS', os.path.abspath("."))
    return os.path.join(base_path, relative_path)

class Transfer:
    def __init__(self, client_name, product_name, quantity, price, cash_paid_now, transfer_id=None, date=None):
        self.transfer_id = transfer_id if transfer_id else str(uuid.uuid4())[:8]
        self.client_name = client_name
        self.product_name = product_name
        self.quantity = quantity
        self.price = price
        self.cash_paid_now = cash_paid_now
        self.date = date if date else datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    def to_dict(self):
        return {
            "transfer_id": self.transfer_id,
            "client_name": self.client_name,
            "product_name": self.product_name,
            "quantity": self.quantity,
            "price": self.price,
            "cash_paid_now": self.cash_paid_now,
            "date": self.date
        }

    def add_transfer(self):
        transfers = self.load_all()
        transfers.append(self)
        self.save_all(transfers)

    def remove_transfer(self):
        transfers = self.load_all()
        transfers = [t for t in transfers if t.transfer_id != self.transfer_id]
        self.save_all(transfers)

    @classmethod
    def load_all(cls):
        transfers = []
        file_path = resource_path("data/Transfers.csv")
        if os.path.exists(file_path):
            with open(file_path, mode='r', newline='') as file:
                reader = csv.DictReader(file)
                for row in reader:
                    transfers.append(cls(
                        client_name=row['client_name'],
                        product_name=row['product_name'],
                        quantity=float(row['quantity']),
                        price=float(row['price']),
                        cash_paid_now=float(row.get('cash_paid_now', 0)),
                        transfer_id=row['transfer_id'],
                        date=row['date']
                    ))
        return transfers

    @classmethod
    def save_all(cls, transfers):
        file_path = resource_path("data/Transfers.csv")
        with open(file_path, mode='w', newline='') as file:
            writer = csv.DictWriter(file, fieldnames=['transfer_id', 'client_name', 'product_name', 'quantity', 'price', 'cash_paid_now', 'date'])
            writer.writeheader()
            for transfer in transfers:
                writer.writerow(transfer.to_dict())