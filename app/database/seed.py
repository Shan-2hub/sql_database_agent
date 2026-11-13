
from datetime import date

from sqlalchemy import (
    MetaData,
    Table,
    Column,
    Integer,
    String,
    Float,
    Date,
    insert,
    select,
)

from app.database.connection import engine

metadata = MetaData()

orders = Table(
    "orders",
    metadata,

    Column("id", Integer, primary_key=True),
    Column("customer_name", String(100), nullable=False),
    Column("product", String(100), nullable=False),
    Column("amount", Float, nullable=False),
    Column("status", String(30), nullable=False),
    Column("order_date", Date, nullable=False),
)


def seed_database():
    """Create tables and insert sample orders."""

    metadata.create_all(engine)

    sample_orders = [
        {
            "id": 1,
            "customer_name": "Arun",
            "product": "Laptop",
            "amount": 65000.0,
            "status": "Completed",
            "order_date": date(2026, 1, 10),
        },
        {
            "id": 2,
            "customer_name": "Priya",
            "product": "Mobile",
            "amount": 25000.0,
            "status": "Completed",
            "order_date": date(2026, 1, 15),
        },
        {
            "id": 3,
            "customer_name": "Karthik",
            "product": "Headphones",
            "amount": 3500.0,
            "status": "Pending",
            "order_date": date(2026, 2, 5),
        },
        {
            "id": 4,
            "customer_name": "Divya",
            "product": "Laptop",
            "amount": 72000.0,
            "status": "Completed",
            "order_date": date(2026, 2, 12),
        },
        {
            "id": 5,
            "customer_name": "Rahul",
            "product": "Keyboard",
            "amount": 2500.0,
            "status": "Cancelled",
            "order_date": date(2026, 3, 1),
        },
        {
            "id": 6,
            "customer_name": "Sneha",
            "product": "Mobile",
            "amount": 30000.0,
            "status": "Completed",
            "order_date": date(2026, 3, 8),
        },
        {
            "id": 7,
            "customer_name": "Vijay",
            "product": "Monitor",
            "amount": 18000.0,
            "status": "Pending",
            "order_date": date(2026, 3, 15),
        },
        {
            "id": 8,
            "customer_name": "Meena",
            "product": "Headphones",
            "amount": 4500.0,
            "status": "Completed",
            "order_date": date(2026, 4, 2),
        },
        {
            "id": 9,
            "customer_name": "Ajay",
            "product": "Laptop",
            "amount": 68000.0,
            "status": "Completed",
            "order_date": date(2026, 4, 10),
        },
        {
            "id": 10,
            "customer_name": "Kavya",
            "product": "Keyboard",
            "amount": 3000.0,
            "status": "Pending",
            "order_date": date(2026, 4, 18),
        },
    ]

    with engine.begin() as connection:
        existing_count = connection.execute(
            select(orders.c.id).limit(1)
        ).first()

        if existing_count is None:
            connection.execute(
                insert(orders),
                sample_orders
            )

    print("Database initialized successfully!")
    print(f"Sample orders available: {len(sample_orders)}")


if __name__ == "__main__":
    seed_database()
