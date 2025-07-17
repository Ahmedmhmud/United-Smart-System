import uuid
from datetime import datetime
import csv
import os
import Order

class Outgoings():
    file_path = Order.resource_path("data/outgoings.csv")
    def __init__(self, name, price, id=None, date=None):
        self.id = id or uuid.uuid4().hex[:8]  
        self.name = name
        self.price = price
        self.date = date or datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name.encode('utf-8').decode('utf-8'),  # Force proper encoding
            'price': self.price,
            'date': self.date
        }

    @classmethod
    def load_all(cls, from_date=None, to_date=None):
        from datetime import datetime
        outgoings = []
 
        if not os.path.exists(cls.file_path):
            return outgoings
        
        # Try multiple encodings
        for encoding in ['utf-8-sig', 'latin-1', 'utf-16']:
            try:
                with open(cls.file_path, mode='r', newline='', encoding=encoding) as file:
                    reader = csv.DictReader(file)
                    for row in reader:
                        try:
                            # Handle potential encoding issues in name
                            name = row['name']
                            if not isinstance(name, str):
                                name = str(name).encode('latin-1').decode('utf-8', errors='replace')
                        
                            # Create outgoing instance
                            outgoing = cls(
                                name=name,
                                price=float(row['price']),
                                id=row['id'],
                                date=row['date']
                            )
                        
                            # Date filtering
                            if from_date or to_date:
                                date_obj = datetime.strptime(outgoing.date, "%Y-%m-%d %H:%M:%S").date()
                                from_date = from_date or datetime.now().date()
                                to_date = to_date or datetime.now().date()
                                if not (from_date <= date_obj <= to_date):
                                    continue
                                
                            outgoings.append(outgoing)
                        except Exception as e:
                            print(f"Skipping corrupt row: {row}. Error: {str(e)}")
                            continue
                    break  # If we got here, encoding worked
            except UnicodeDecodeError:
                continue
        return outgoings
    
    @classmethod
    def save_all(cls, outgoings):
        with open(cls.file_path, mode='w', newline='', encoding='utf-8-sig') as file:  # Added encoding
            writer = csv.DictWriter(file, fieldnames=['id', 'name', 'price', 'date'])
            writer.writeheader()
            for outgoing in outgoings:
                writer.writerow(outgoing.to_dict())