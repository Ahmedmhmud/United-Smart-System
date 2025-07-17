import os
import csv
import uuid
import Order

class Client():
    file_path = Order.resource_path("data/clients.csv")

    def __init__(self, name, phone, role, id=None, previous_balance=0.0):
        self.name = name
        self.phone = phone
        self.role = role
        self.id = id if id else str(uuid.uuid4())[:8]
        self.previous_balance = previous_balance


    def to_dict(self):
        return {'Name': self.name, 'Phone': self.phone, 'Role': self.role, 'ID': self.id, 'Previous Balance': self.previous_balance}
    
    @classmethod
    def load_all(cls):
        clients = []
        if os.path.exists(cls.file_path):
            with open(cls.file_path, mode='r', newline='') as file:
                reader = csv.DictReader(file)
                for row in reader:
                    try:
                        clients.append(cls(
                            name=row['Name'],
                            phone=row['Phone'],
                            role=row['Role'],
                            id=row['ID'],
                            previous_balance=float(row['Previous Balance'])
                        ))
                    except (KeyError, ValueError) as e:
                        print(f"Skipping corrupted row: {row} due to error: {e}")
        return clients

    @classmethod
    def save_all(cls, clients):
        with open(cls.file_path, mode='w', newline='') as file:
            writer = csv.DictWriter(file, fieldnames=['Name', 'Phone', 'Role', 'ID', 'Previous Balance'])
            writer.writeheader()
            for client in clients:
                writer.writerow(client.to_dict())

    def add_client(self):
        clients = self.load_all()
        clients.append(self)
        self.save_all(clients)

    def remove_client(self):
        clients = self.load_all()
        clients = [c for c in clients if not (c.id == self.id)]
        self.save_all(clients)

    def edit_client(self, new_name, new_phone, new_role):
        self.name = new_name
        self.phone = new_phone
        self.role = new_role
        self._update_in_file()
    
    def _update_in_file(self):
        clients = self.load_all()
        for i, c in enumerate(clients):
            if c.id == self.id:
                clients[i] = self
                break
        self.save_all(clients)
    
    @classmethod
    def initialize_file(cls):
        if not os.path.exists(cls.file_path):
            with open(cls.file_path, mode='w', newline='') as file:
                writer = csv.DictWriter(file, fieldnames=['Name', 'Phone', 'Role', 'ID', 'Previous Balance'])
                writer.writeheader()