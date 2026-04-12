"""Tests for database module."""

import sqlite3
import tempfile
import os
import pytest
from flask import Flask

from database.db import get_db, close_db, init_db, seed_db


@pytest.fixture
def app():
    """Create a Flask app with temporary database for testing."""
    db_fd, db_path = tempfile.mkstemp()
    app = Flask(__name__)
    app.config['DATABASE'] = db_path
    app.config['TESTING'] = True

    with app.app_context():
        init_db()

    yield app

    os.close(db_fd)
    os.unlink(db_path)


@pytest.fixture
def client(app):
    """Create a test client for the app."""
    return app.test_client()


def test_get_db_returns_connection(app):
    """Test that get_db returns a valid SQLite connection."""
    with app.app_context():
        db = get_db()
        assert db is not None
        assert isinstance(db, sqlite3.Connection)


def test_get_db_row_factory(app):
    """Test that get_db sets sqlite3.Row as row_factory."""
    with app.app_context():
        db = get_db()
        assert db.row_factory == sqlite3.Row


def test_get_db_foreign_keys_enabled(app):
    """Test that foreign key enforcement is enabled."""
    with app.app_context():
        db = get_db()
        result = db.execute('PRAGMA foreign_keys').fetchone()
        assert result[0] == 1


def test_get_db_caches_connection(app):
    """Test that get_db caches the connection in flask.g."""
    with app.app_context():
        db1 = get_db()
        db2 = get_db()
        assert db1 is db2


def test_close_db(app):
    """Test that close_db removes the connection from g."""
    from flask import g
    with app.app_context():
        db = get_db()
        assert 'db' in g
        close_db()
        assert 'db' not in g


def test_init_db_creates_users_table(app):
    """Test that init_db creates the users table."""
    with app.app_context():
        db = get_db()
        result = db.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name='users'"
        ).fetchone()
        assert result is not None
        assert result['name'] == 'users'


def test_init_db_creates_expenses_table(app):
    """Test that init_db creates the expenses table."""
    with app.app_context():
        db = get_db()
        result = db.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name='expenses'"
        ).fetchone()
        assert result is not None
        assert result['name'] == 'expenses'


def test_users_table_schema(app):
    """Test that users table has correct columns."""
    with app.app_context():
        db = get_db()
        result = db.execute("PRAGMA table_info(users)").fetchall()
        columns = {row['name'] for row in result}
        assert 'id' in columns
        assert 'name' in columns
        assert 'email' in columns
        assert 'password_hash' in columns
        assert 'created_at' in columns


def test_expenses_table_schema(app):
    """Test that expenses table has correct columns."""
    with app.app_context():
        db = get_db()
        result = db.execute("PRAGMA table_info(expenses)").fetchall()
        columns = {row['name'] for row in result}
        assert 'id' in columns
        assert 'user_id' in columns
        assert 'amount' in columns
        assert 'category' in columns
        assert 'description' in columns
        assert 'date' in columns
        assert 'created_at' in columns


def test_expenses_foreign_key(app):
    """Test that expenses table has foreign key constraint."""
    with app.app_context():
        db = get_db()
        # Insert a user first
        db.execute(
            'INSERT INTO users (name, email, password_hash) VALUES (?, ?, ?)',
            ('Test User', 'test@example.com', 'hash')
        )
        db.commit()

        # Insert an expense with valid user_id
        db.execute(
            'INSERT INTO expenses (user_id, amount, category, date) VALUES (?, ?, ?, ?)',
            (1, 100.0, 'Food', '2025-04-10')
        )
        db.commit()

        # Verify expense was inserted
        result = db.execute('SELECT * FROM expenses WHERE user_id = 1').fetchone()
        assert result is not None


def test_seed_db_inserts_users(app):
    """Test that seed_db inserts demo user."""
    with app.app_context():
        seed_db()
        db = get_db()
        users = db.execute('SELECT * FROM users').fetchall()
        assert len(users) == 1  # Only Demo User
        assert users[0]['name'] == 'Demo User'
        assert users[0]['email'] == 'demo@spendly.com'


def test_seed_db_inserts_expenses(app):
    """Test that seed_db inserts 8 sample expenses."""
    with app.app_context():
        seed_db()
        db = get_db()
        expenses = db.execute('SELECT * FROM expenses').fetchall()
        assert len(expenses) == 8  # Exactly 8 expenses


def test_seed_db_is_idempotent(app):
    """Test that seed_db doesn't duplicate data when run multiple times."""
    with app.app_context():
        seed_db()
        first_user_count = get_db().execute('SELECT COUNT(*) FROM users').fetchone()[0]
        first_expense_count = get_db().execute('SELECT COUNT(*) FROM expenses').fetchone()[0]

        seed_db()  # Run again
        second_user_count = get_db().execute('SELECT COUNT(*) FROM users').fetchone()[0]
        second_expense_count = get_db().execute('SELECT COUNT(*) FROM expenses').fetchone()[0]

        assert first_user_count == second_user_count
        assert first_expense_count == second_expense_count
