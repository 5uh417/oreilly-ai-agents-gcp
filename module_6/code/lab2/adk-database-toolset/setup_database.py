# setup_database.py
import sqlite3
import os

DB_FILE = "products.db"

# Delete the database file if it exists to ensure a clean start
if os.path.exists(DB_FILE):
    os.remove(DB_FILE)

# Connect to the SQLite database (this will create the file)
conn = sqlite3.connect(DB_FILE)
cursor = conn.cursor()

# Create the 'products' table
cursor.execute("""
CREATE TABLE products (
    id INTEGER PRIMARY KEY,
    name TEXT NOT NULL,
    category TEXT NOT NULL,
    price REAL NOT NULL,
    stock_quantity INTEGER NOT NULL
);
""")

# Sample product data
products_data = [
    ('Virtual Reality Headset', 'Electronics', 349.99, 150),
    ('Smart Coffee Maker', 'Home Goods', 89.50, 200),
    ('Wireless Noise-Cancelling Headphones', 'Electronics', 249.99, 300),
    ('Robotic Vacuum Cleaner', 'Home Goods', 199.99, 120),
    ('4K Action Camera', 'Electronics', 175.00, 250),
    ('LED Desk Lamp', 'Home Goods', 45.99, 500),
    ('Portable Bluetooth Speaker', 'Electronics', 65.25, 400)
]

# Insert the data into the table
cursor.executemany("""
INSERT INTO products (name, category, price, stock_quantity)
VALUES (?, ?, ?, ?);
""", products_data)

# Commit the changes and close the connection
conn.commit()
conn.close()

print(f"Database '{DB_FILE}' created and populated successfully.")
print(f"Absolute path: {os.path.abspath(DB_FILE)}")
