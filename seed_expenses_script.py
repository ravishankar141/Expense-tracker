#!/usr/bin/env python3
"""Seed expenses script for Spendly expense tracker."""

import sqlite3
import random
from datetime import datetime, timedelta

DATABASE = 'spendly.db'


# Category definitions with amount ranges and distribution weights
CATEGORIES = {
    'Food': (50, 800, 30),         # Most common
    'Transport': (20, 500, 20),
    'Bills': (200, 3000, 15),
    'Shopping': (200, 5000, 15),
    'Health': (100, 2000, 8),      # Least common
    'Entertainment': (100, 1500, 8),
    'Other': (50, 1500, 4),
}

# Realistic Indian descriptions per category
DESCRIPTIONS = {
    'Food': ['Lunch at cafe', 'Dinner at restaurant', 'Street food', 'Groceries', 'Bakery items', 'Coffee and snacks', 'Family dinner', 'Tiffin service'],
    'Transport': ['Auto rickshaw', 'Uber ride', 'Metro card', 'Bus pass', 'Fuel', 'Taxi', 'Ola cab', 'Bike maintenance'],
    'Bills': ['Electricity bill', 'Water bill', 'Internet bill', 'Mobile recharge', 'Gas cylinder', 'Maintenance charges', 'Insurance premium'],
    'Health': ['Pharmacy', 'Doctor consultation', 'Lab tests', 'Vitamins', 'Gym membership', 'Medical equipment'],
    'Entertainment': ['Movie tickets', 'Concert', 'Streaming subscription', 'Game purchase', 'Books', 'Weekend trip'],
    'Shopping': ['Clothes', 'Electronics', 'Home decor', 'Kitchen items', 'Personal care', 'Gifts', 'Furniture'],
    'Other': ['Misc items', 'Donations', 'Pet supplies', 'Stationery', 'Repairs', 'Emergency expense'],
}


def get_db():
    """Get a SQLite database connection."""
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
    conn.execute('PRAGMA foreign_keys = ON')
    return conn


def verify_user_exists(user_id):
    """Check if user exists in database."""
    db = get_db()
    user = db.execute(
        'SELECT id, name, email FROM users WHERE id = ?',
        (user_id,)
    ).fetchone()
    db.close()
    return user


def generate_expenses(user_id, count, months):
    """Generate expense records spread across past months."""
    expenses = []

    # Calculate date range
    today = datetime.now()
    start_date = today - timedelta(days=months * 30)

    # Build weighted category list for distribution
    weighted_categories = []
    for cat, (_, _, weight) in CATEGORIES.items():
        weighted_categories.extend([cat] * weight)

    for i in range(count):
        # Random date within range
        days_offset = random.randint(0, months * 30)
        expense_date = start_date + timedelta(days=days_offset)

        # Random category (weighted)
        category = random.choice(weighted_categories)

        # Random amount within category range
        min_amt, max_amt, _ = CATEGORIES[category]
        amount = round(random.uniform(min_amt, max_amt), 2)

        # Random description
        description = random.choice(DESCRIPTIONS[category])

        expenses.append((
            user_id,
            amount,
            category,
            expense_date.strftime('%Y-%m-%d'),
            description
        ))

    return expenses


def insert_expenses(expenses):
    """Insert all expenses in a single transaction."""
    db = get_db()
    try:
        db.executemany(
            '''INSERT INTO expenses (user_id, amount, category, date, description)
               VALUES (?, ?, ?, ?, ?)''',
            expenses
        )
        db.commit()
        return True
    except Exception as e:
        db.rollback()
        print(f"Error inserting expenses: {e}")
        return False
    finally:
        db.close()


def main():
    import sys

    # Parse arguments
    if len(sys.argv) < 3:
        print("Usage: python seed_expenses_script.py <user_id> <count> [months]")
        print("Example: python seed_expenses_script.py 1 50 6")
        sys.exit(1)

    user_id = int(sys.argv[1])
    count = int(sys.argv[2])
    months = int(sys.argv[3]) if len(sys.argv) > 3 else 6

    # Verify user exists
    user = verify_user_exists(user_id)
    if not user:
        print(f"No user found with id {user_id}.")
        sys.exit(1)

    print(f"User found: {user['name']} ({user['email']})")
    print(f"Generating {count} expenses across {months} months...")

    # Generate expenses
    expenses = generate_expenses(user_id, count, months)

    # Insert expenses
    if insert_expenses(expenses):
        # Get date range from inserted expenses
        dates = [exp[3] for exp in expenses]
        min_date = min(dates)
        max_date = max(dates)

        print(f"\n✓ Successfully inserted {count} expenses")
        print(f"Date range: {min_date} to {max_date}")
        print("\nSample records (first 5):")
        print("-" * 70)
        for exp in expenses[:5]:
            print(f"  {exp[3]} | ₹{exp[1]:.2f} | {exp[2]:<15} | {exp[4]}")
        print("-" * 70)
    else:
        print("Failed to insert expenses (transaction rolled back)")
        sys.exit(1)


if __name__ == '__main__':
    main()
