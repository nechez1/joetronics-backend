import sqlite3
from datetime import datetime

def initialize_db():
    conn = sqlite3.connect('orders.db')
    c = conn.cursor()
    c.execute('''
        CREATE TABLE IF NOT EXISTS orders (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            reference TEXT,
            email TEXT,
            item_name TEXT,
            quantity INTEGER,
            price INTEGER,
            date TEXT
        )
    ''')
    conn.commit()
    conn.close()

def save_order(reference, email, items):
    conn = sqlite3.connect('orders.db')
    c = conn.cursor()
    date = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

    for item in items:
        name = item.get('name') or item.get('display_name') or "Unknown"
        quantity = int(item.get('quantity', 1))
        price = int(item.get('price', 0))
        
        c.execute('''
            INSERT INTO orders (reference, email, item_name, quantity, price, date)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', (reference, email, name, quantity, price, date))

    conn.commit()
    conn.close()
