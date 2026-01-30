#!/usr/bin/env python3
"""
Create sample SQLite database for testing.

Usage:
    python scripts/create_sample_db.py
"""

import sqlite3
from pathlib import Path
from datetime import datetime, timedelta
import random


def create_sample_database(db_path: Path):
    """Create a sample SQLite database with test data."""
    print(f"Creating sample database: {db_path}")

    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    # Create users table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            email TEXT UNIQUE,
            age INTEGER,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            is_active INTEGER DEFAULT 1
        )
    ''')

    # Create orders table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS orders (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            product_name TEXT NOT NULL,
            quantity INTEGER DEFAULT 1,
            price REAL NOT NULL,
            order_date DATETIME DEFAULT CURRENT_TIMESTAMP,
            status TEXT DEFAULT 'pending',
            FOREIGN KEY (user_id) REFERENCES users(id)
        )
    ''')

    # Create products table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS products (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            description TEXT,
            price REAL NOT NULL,
            stock INTEGER DEFAULT 0,
            category TEXT
        )
    ''')

    # Create indexes
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_users_email ON users(email)')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_orders_user_id ON orders(user_id)')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_orders_status ON orders(status)')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_products_category ON products(category)')

    # Insert sample users
    users = [
        ('Alice Kim', 'alice@example.com', 28),
        ('Bob Lee', 'bob@example.com', 35),
        ('Charlie Park', 'charlie@example.com', 42),
        ('Diana Choi', 'diana@example.com', 31),
        ('Edward Jung', 'edward@example.com', 25),
        ('Fiona Han', 'fiona@example.com', 29),
        ('George Yoon', 'george@example.com', 38),
        ('Helen Shin', 'helen@example.com', 33),
        ('Ivan Song', 'ivan@example.com', 27),
        ('Julia Kang', 'julia@example.com', 45),
    ]

    cursor.executemany('''
        INSERT OR IGNORE INTO users (name, email, age)
        VALUES (?, ?, ?)
    ''', users)

    # Insert sample products
    products = [
        ('Laptop', 'High-performance laptop', 1299.99, 50, 'Electronics'),
        ('Mouse', 'Wireless optical mouse', 29.99, 200, 'Electronics'),
        ('Keyboard', 'Mechanical keyboard', 89.99, 150, 'Electronics'),
        ('Monitor', '27-inch 4K display', 499.99, 30, 'Electronics'),
        ('Headphones', 'Noise-canceling headphones', 199.99, 80, 'Electronics'),
        ('Desk', 'Standing desk', 399.99, 25, 'Furniture'),
        ('Chair', 'Ergonomic office chair', 299.99, 40, 'Furniture'),
        ('Lamp', 'LED desk lamp', 49.99, 100, 'Furniture'),
        ('Notebook', 'Spiral notebook', 9.99, 500, 'Stationery'),
        ('Pen Set', 'Premium pen set', 24.99, 300, 'Stationery'),
    ]

    cursor.executemany('''
        INSERT OR IGNORE INTO products (name, description, price, stock, category)
        VALUES (?, ?, ?, ?, ?)
    ''', products)

    # Insert sample orders
    statuses = ['pending', 'confirmed', 'shipped', 'delivered', 'cancelled']
    product_names = [p[0] for p in products]
    product_prices = {p[0]: p[2] for p in products}

    orders = []
    base_date = datetime.now() - timedelta(days=90)

    for i in range(100):
        user_id = random.randint(1, len(users))
        product = random.choice(product_names)
        quantity = random.randint(1, 5)
        price = product_prices[product] * quantity
        order_date = base_date + timedelta(days=random.randint(0, 90))
        status = random.choice(statuses)

        orders.append((user_id, product, quantity, price, order_date.isoformat(), status))

    cursor.executemany('''
        INSERT INTO orders (user_id, product_name, quantity, price, order_date, status)
        VALUES (?, ?, ?, ?, ?, ?)
    ''', orders)

    # Create a view
    cursor.execute('''
        CREATE VIEW IF NOT EXISTS user_order_summary AS
        SELECT
            u.name as user_name,
            u.email,
            COUNT(o.id) as order_count,
            COALESCE(SUM(o.price), 0) as total_spent
        FROM users u
        LEFT JOIN orders o ON u.id = o.user_id
        GROUP BY u.id
    ''')

    conn.commit()
    conn.close()

    print(f"  Created tables: users, orders, products")
    print(f"  Created view: user_order_summary")
    print(f"  Inserted: {len(users)} users, {len(products)} products, {len(orders)} orders")
    print("Done!")


def main():
    project_root = Path(__file__).parent.parent
    data_dir = project_root / "data" / "sample"
    data_dir.mkdir(parents=True, exist_ok=True)

    db_path = data_dir / "sample.db"
    create_sample_database(db_path)


if __name__ == "__main__":
    main()
