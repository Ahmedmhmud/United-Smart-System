import csv
import os
import Order

class Product:
    file_path = Order.resource_path("data/Products.csv")

    def __init__(self, name, price, quantity):
        self.name = name
        self.price = float(price)
        self.quantity = float(quantity)

    def to_dict(self):
        return {'Name': self.name, 'Price': self.price, 'Quantity': self.quantity}
    
    @classmethod
    def from_dict(cls, data):
        return cls(data['Name'], data['Price'], data['Quantity'])

    @classmethod
    def load_all(cls):
        products = []
        if os.path.exists(cls.file_path):
            with open(cls.file_path, mode='r', newline='') as file:
                reader = csv.DictReader(file)
                for row in reader:
                    products.append(Product(row['Name'], row['Price'], row['Quantity']))
        return products

    @classmethod
    def save_all(cls, products):
        with open(cls.file_path, mode='w', newline='') as file:
            writer = csv.DictWriter(file, fieldnames=['Name', 'Price', 'Quantity'])
            writer.writeheader()
            for product in products:
                writer.writerow(product.to_dict())

    def add_product(self):
        products = self.load_all()
        products.append(self)
        self.save_all(products)

    def remove_product(self):
        products = self.load_all()
        products = [p for p in products if not (p.name == self.name)]
        self.save_all(products)

    def update_quantity(self, new_quantity):
        self.quantity = new_quantity
        self._update_in_file()

    def update_price(self, new_price):
        self.price = new_price
        self._update_in_file()

    def edit_product(self, new_name, new_price, new_quantity):
        self.name = new_name
        self.price = new_price
        self.quantity = new_quantity
        self._update_in_file()

    def _update_in_file(self):
        products = self.load_all()
        for i, p in enumerate(products):
            if p.name == self.name:
                products[i] = self
                break
        self.save_all(products)

    @classmethod
    def initialize_file(cls):
        if not os.path.exists(cls.file_path):
            with open(cls.file_path, mode='w', newline='') as file:
                writer = csv.DictWriter(file, fieldnames=['Name', 'Price', 'Quantity'])
                writer.writeheader()
