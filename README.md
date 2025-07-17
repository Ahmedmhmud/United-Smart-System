# United Smart System

A desktop-based smart financial management system built with Python. The system features a user-friendly GUI and robust backend logic to manage clients, orders, transfers, outgoings, and treasury operations. All data is securely stored in local files and can be viewed, filtered, and exported in multiple formats.

---

## 🧠 Core Features

- 🔐 **Admin Panel**  
  Admin can:
  - Add/edit/delete **clients**, **orders**, **transfers**, and **outgoings**
  - Automatically update and track the **treasury/budget**
  - Search and filter operations by **date**

- 📁 **File-Based Data Storage**
  - `clients.csv`: Stores client information  
  - `products.csv`: Stores product inventory  
  - `orders.json`: Stores all orders (with full product lists)  
  - `transfers.csv`: Records client-to-client or internal transfers  
  - `outgoings.csv`: Tracks expenditures  
  - `login.txt`: Admin authentication credentials  

- 📊 **Treasury Management**
  - Real-time treasury calculation based on all financial operations  
  - Visual budget overview through the GUI  

- 🖥️ **Graphical User Interface (GUI)**
  - Clean and organized interface for managing all operations  
  - Dynamic views of data with sorting and formatting  
  - Filters by date for all transactions  

- 🧾 **PDF Export**
  - Orders can be exported as well-formatted **PDF receipts**  
  - Useful for printing or sharing with clients  

---

## 🏗️ Class Structure

| Class      | Description                                                                 |
|------------|-----------------------------------------------------------------------------|
| `Admin`    | Handles high-level operations: add/edit/delete clients, orders, etc.        |
| `App`      | Main GUI logic – builds the interface, handles user actions                 |
| `Clients`  | Manages client data and file persistence                                    |
| `Transfer` | Models and processes transfers, adjusts treasury and client balances        |
| `Outgoings`| Represents and stores expenditure records                                    |
| `Order`    | Manages product orders, including totals and file export                    |
| `Product`  | Stores product details and supports quantity/price logic                    |
| `Treasury` | Calculates and tracks the total budget based on all financial activity      |

---

## 📦 Requirements

- Python 3.9+
- Libraries:
  - `customtkinter` (GUI framework)
  - `reportlab` (for PDF export)
  - `datetime`, `uuid`, `csv`, `json` (built-in)
