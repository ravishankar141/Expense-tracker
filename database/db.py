"""Database module for Spendly expense tracker.

Provides SQLite database helpers for connection management,
table creation, and sample data seeding.
"""

import sqlite3
from flask import g, current_app
from werkzeug.security import generate_password_hash

DATABASE = 'spendly.db'


def get_db():
    """Get a SQLite database connection with row factory and foreign keys enabled.

    Returns:
        sqlite3.Connection: Database connection with sqlite3.Row row_factory
                             and foreign key enforcement enabled.
    """
    if 'db' not in g:
        g.db = sqlite3.connect(
            current_app.config.get('DATABASE', DATABASE),
            detect_types=sqlite3.PARSE_DECLTYPES
        )
        g.db.row_factory = sqlite3.Row
        g.db.execute('PRAGMA foreign_keys = ON')
    return g.db


def close_db(_e=None):
    """Close the database connection.

    Should be registered with Flask's teardown_appcontext.

    Args:
        _e: Exception if teardown was triggered by an exception (unused).
    """
    db = g.pop('db', None)
    if db is not None:
        db.close()


def init_db():
    """Initialize the database by creating all tables.

    Uses CREATE TABLE IF NOT EXISTS so it's safe to call multiple times.
    """
    db = get_db()

    # Create users table
    db.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            email TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')

    # Create expenses table with foreign key to users
    db.execute('''
        CREATE TABLE IF NOT EXISTS expenses (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            amount REAL NOT NULL,
            category TEXT NOT NULL,
            date TEXT NOT NULL,
            description TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
        )
    ''')

    db.commit()


def seed_db():
    """Seed the database with sample data for development.

    Only inserts data if tables are empty (idempotent).
    """
    db = get_db()

    # Check if users table already has data
    user_count = db.execute('SELECT COUNT(*) FROM users').fetchone()[0]
    if user_count > 0:
        return  # Already has data, skip seeding

    # Insert demo user with hashed password
    password_hash = generate_password_hash('demo123')
    db.execute(
        'INSERT INTO users (name, email, password_hash) VALUES (?, ?, ?)',
        ('Demo User', 'demo@spendly.com', password_hash)
    )

    # Get demo user ID for expense insertion
    demo_user_id = db.execute(
        'SELECT id FROM users WHERE email = ?',
        ('demo@spendly.com',)
    ).fetchone()[0]

    # Insert 8 sample expenses across categories
    sample_expenses = [
        (demo_user_id, 45.50, 'Food', '2025-04-01', 'Lunch at cafe'),
        (demo_user_id, 120.00, 'Transport', '2025-04-03', 'Monthly bus pass'),
        (demo_user_id, 85.00, 'Bills', '2025-04-05', 'Electric bill'),
        (demo_user_id, 55.00, 'Health', '2025-04-06', 'Pharmacy'),
        (demo_user_id, 35.00, 'Entertainment', '2025-04-08', 'Movie tickets'),
        (demo_user_id, 150.00, 'Shopping', '2025-04-10', 'Groceries'),
        (demo_user_id, 25.00, 'Other', '2025-04-11', 'Misc items'),
        (demo_user_id, 60.00, 'Food', '2025-04-12', 'Dinner'),
    ]

    for expense in sample_expenses:
        db.execute(
            '''INSERT INTO expenses
               (user_id, amount, category, date, description)
               VALUES (?, ?, ?, ?, ?)''',
            expense
        )

    db.commit()


def create_user(name: str, email: str, password: str) -> int:
    """Create a new user with hashed password.

    Args:
        name: User's full name.
        email: User's email address (must be unique).
        password: Plaintext password to be hashed.

    Returns:
        int: The new user's ID.

    Raises:
        sqlite3.IntegrityError: If email already exists.
    """
    db = get_db()
    password_hash = generate_password_hash(password)
    cursor = db.execute(
        'INSERT INTO users (name, email, password_hash) VALUES (?, ?, ?)',
        (name, email, password_hash)
    )
    db.commit()
    return cursor.lastrowid
