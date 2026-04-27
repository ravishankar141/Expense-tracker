"""Tests for backend connection and query functions."""

import sqlite3
import tempfile
import os
import pytest
from flask import Flask

from database.db import get_db, init_db, seed_db, close_db
from database.queries import get_summary_stats, get_recent_transactions, get_category_breakdown, get_user_by_id
from werkzeug.security import generate_password_hash


@pytest.fixture
def app():
    """Create a Flask app with temporary database for testing."""
    db_fd, db_path = tempfile.mkstemp()

    # Import and configure the actual app
    from app import app as application
    application.config['DATABASE'] = db_path
    application.config['TESTING'] = True
    application.secret_key = 'test-secret-key'

    with application.app_context():
        init_db()

    yield application

    os.close(db_fd)
    os.unlink(db_path)


@pytest.fixture
def seeded_app():
    """Create a Flask app with seeded database for testing."""
    db_fd, db_path = tempfile.mkstemp()

    # Import and configure the actual app
    from app import app as application
    application.config['DATABASE'] = db_path
    application.config['TESTING'] = True
    application.secret_key = 'test-secret-key'

    with application.app_context():
        init_db()
        seed_db()

    yield application

    os.close(db_fd)
    os.unlink(db_path)


def test_get_summary_stats_with_expenses(seeded_app):
    """Test that get_summary_stats returns correct totals for user with expenses."""
    with seeded_app.app_context():
        db = get_db()
        # Get the demo user ID
        demo_user = db.execute(
            'SELECT id FROM users WHERE email = ?',
            ('demo@spendly.com',)
        ).fetchone()
        user_id = demo_user['id']

        stats = get_summary_stats(user_id)

        # Verify total_spent (45.50 + 120.00 + 85.00 + 55.00 + 35.00 + 150.00 + 25.00 + 60.00 = 575.50)
        assert stats['total_spent'] == 575.50

        # Verify transaction_count (8 expenses)
        assert stats['transaction_count'] == 8

        # Verify top_category (Shopping has 150.00, highest single category)
        assert stats['top_category'] == 'Shopping'


def test_get_summary_stats_no_expenses(app):
    """Test that get_summary_stats returns zeros and em-dash for user with no expenses."""
    with app.app_context():
        db = get_db()
        # Create a user with no expenses
        db.execute(
            'INSERT INTO users (name, email, password_hash) VALUES (?, ?, ?)',
            ('No Expense User', 'noexpense@example.com', 'hash')
        )
        db.commit()

        new_user = db.execute(
            'SELECT id FROM users WHERE email = ?',
            ('noexpense@example.com',)
        ).fetchone()
        user_id = new_user['id']

        stats = get_summary_stats(user_id)

        # Verify zeros for totals
        assert stats['total_spent'] == 0.0
        assert stats['transaction_count'] == 0

        # Verify em-dash for top_category
        assert stats['top_category'] == '—'


def test_get_summary_stats_returns_dict(app):
    """Test that get_summary_stats returns a dict with correct keys."""
    with app.app_context():
        db = get_db()
        # Create a user with no expenses
        db.execute(
            'INSERT INTO users (name, email, password_hash) VALUES (?, ?, ?)',
            ('Test User', 'test@example.com', 'hash')
        )
        db.commit()

        user = db.execute(
            'SELECT id FROM users WHERE email = ?',
            ('test@example.com',)
        ).fetchone()

        stats = get_summary_stats(user['id'])

        # Verify return type is dict
        assert isinstance(stats, dict)

        # Verify all required keys are present
        assert 'total_spent' in stats
        assert 'transaction_count' in stats
        assert 'top_category' in stats


def test_get_summary_stats_nonexistent_user(app):
    """Test that get_summary_stats handles nonexistent user gracefully."""
    with app.app_context():
        # Use a user ID that doesn't exist
        stats = get_summary_stats(99999)

        # Should return zeros and em-dash
        assert stats['total_spent'] == 0.0
        assert stats['transaction_count'] == 0
        assert stats['top_category'] == '—'


class TestGetRecentTransactions:
    """Tests for get_recent_transactions function."""

    def test_get_recent_transactions_with_expenses(self, seeded_app):
        """Test that get_recent_transactions returns list ordered newest-first."""
        with seeded_app.app_context():
            db = get_db()
            # Get the demo user ID
            user = db.execute(
                'SELECT id FROM users WHERE email = ?',
                ('demo@spendly.com',)
            ).fetchone()
            user_id = user['id']

            # Fetch recent transactions
            transactions = get_recent_transactions(user_id)

            # Should return a list
            assert isinstance(transactions, list)

            # Should have transactions (seed_db creates 8 expenses)
            assert len(transactions) > 0

            # Each transaction should have required keys
            for txn in transactions:
                assert 'date' in txn
                assert 'description' in txn
                assert 'category' in txn
                assert 'amount' in txn

            # Should be ordered by date DESC (newest first)
            dates = [txn['date'] for txn in transactions]
            assert dates == sorted(dates, reverse=True)

            # Most recent expense should be "Dinner" on 2025-04-12
            assert transactions[0]['date'] == '2025-04-12'
            assert transactions[0]['description'] == 'Dinner'
            assert transactions[0]['category'] == 'Food'
            assert transactions[0]['amount'] == 60.00

    def test_get_recent_transactions_empty(self, app):
        """Test that get_recent_transactions returns empty list for user with no expenses."""
        with app.app_context():
            db = get_db()

            # Create a new user with no expenses
            db.execute(
                'INSERT INTO users (name, email, password_hash) VALUES (?, ?, ?)',
                ('Empty User', 'empty@example.com', 'hash')
            )
            db.commit()

            # Get the new user's ID
            user = db.execute(
                'SELECT id FROM users WHERE email = ?',
                ('empty@example.com',)
            ).fetchone()
            user_id = user['id']

            # Fetch transactions for user with no expenses
            transactions = get_recent_transactions(user_id)

            # Should return empty list
            assert transactions == []
            assert isinstance(transactions, list)

    def test_get_recent_transactions_limit(self, seeded_app):
        """Test that get_recent_transactions respects the limit parameter."""
        with seeded_app.app_context():
            db = get_db()
            user = db.execute(
                'SELECT id FROM users WHERE email = ?',
                ('demo@spendly.com',)
            ).fetchone()
            user_id = user['id']

            # Fetch with limit of 3
            transactions = get_recent_transactions(user_id, limit=3)

            # Should return exactly 3 transactions
            assert len(transactions) == 3

            # Should still be ordered newest-first
            dates = [txn['date'] for txn in transactions]
            assert dates == sorted(dates, reverse=True)


class TestGetCategoryBreakdown:
    """Tests for get_category_breakdown function."""

    def test_get_category_breakdown_with_expenses(self, seeded_app):
        """Test that get_category_breakdown returns category spending data."""
        with seeded_app.app_context():
            db = get_db()
            user = db.execute(
                'SELECT id FROM users WHERE email = ?',
                ('demo@spendly.com',)
            ).fetchone()
            user_id = user['id']

            breakdown = get_category_breakdown(user_id)

            # Should return a list
            assert isinstance(breakdown, list)
            assert len(breakdown) > 0

            # Each category should have required keys
            for cat in breakdown:
                assert 'name' in cat
                assert 'amount' in cat
                assert 'percentage' in cat

            # Percentages should sum to 100
            total_percentage = sum(cat['percentage'] for cat in breakdown)
            assert total_percentage == 100

    def test_get_category_breakdown_empty(self, app):
        """Test that get_category_breakdown returns empty list for user with no expenses."""
        with app.app_context():
            db = get_db()

            # Create a new user with no expenses
            db.execute(
                'INSERT INTO users (name, email, password_hash) VALUES (?, ?, ?)',
                ('Empty User', 'empty2@example.com', 'hash')
            )
            db.commit()

            user = db.execute(
                'SELECT id FROM users WHERE email = ?',
                ('empty2@example.com',)
            ).fetchone()
            user_id = user['id']

            breakdown = get_category_breakdown(user_id)

            assert breakdown == []


class TestGetUserById:
    """Tests for get_user_by_id function."""

    def test_get_user_by_id_exists(self, seeded_app):
        """Test that get_user_by_id returns correct user data."""
        with seeded_app.app_context():
            db = get_db()
            user = db.execute(
                'SELECT id FROM users WHERE email = ?',
                ('demo@spendly.com',)
            ).fetchone()
            user_id = user['id']

            result = get_user_by_id(user_id)

            assert result is not None
            assert result['name'] == 'Demo User'
            assert result['email'] == 'demo@spendly.com'
            assert 'member_since' in result  # Should be formatted date

    def test_get_user_by_id_not_found(self, app):
        """Test that get_user_by_id returns None for nonexistent user."""
        with app.app_context():
            result = get_user_by_id(99999)
            assert result is None


class TestProfileRoute:
    """Tests for the /profile route."""

    def test_profile_unauthenticated_redirects(self, seeded_app):
        """Test that unauthenticated access to /profile redirects to /login."""
        with seeded_app.test_client() as client:
            response = client.get('/profile')
            assert response.status_code == 302
            assert '/login' in response.headers['Location']

    def test_profile_authenticated_returns_200(self, seeded_app):
        """Test that authenticated access to /profile returns 200."""
        with seeded_app.test_client() as client:
            # Login first
            client.post('/login', data={
                'email': 'demo@spendly.com',
                'password': 'demo123'
            }, follow_redirects=False)

            # Now access profile
            response = client.get('/profile')
            assert response.status_code == 200

    def test_profile_shows_real_user_data(self, seeded_app):
        """Test that profile shows real user name and email."""
        with seeded_app.test_client() as client:
            # Login
            client.post('/login', data={
                'email': 'demo@spendly.com',
                'password': 'demo123'
            }, follow_redirects=False)

            response = client.get('/profile')
            data = response.get_data(as_text=True)

            assert 'Demo User' in data
            assert 'demo@spendly.com' in data

    def test_profile_shows_rupee_symbol(self, seeded_app):
        """Test that profile page displays rupee symbol."""
        with seeded_app.test_client() as client:
            client.post('/login', data={
                'email': 'demo@spendly.com',
                'password': 'demo123'
            }, follow_redirects=False)

            response = client.get('/profile')
            data = response.get_data(as_text=True)

            assert '₹' in data

    def test_profile_shows_correct_total_spent(self, seeded_app):
        """Test that profile shows correct total spent (575.50)."""
        with seeded_app.test_client() as client:
            client.post('/login', data={
                'email': 'demo@spendly.com',
                'password': 'demo123'
            }, follow_redirects=False)

            response = client.get('/profile')
            data = response.get_data(as_text=True)

            assert '575.50' in data

    def test_profile_shows_correct_transaction_count(self, seeded_app):
        """Test that profile shows 8 transactions."""
        with seeded_app.test_client() as client:
            client.post('/login', data={
                'email': 'demo@spendly.com',
                'password': 'demo123'
            }, follow_redirects=False)

            response = client.get('/profile')
            data = response.get_data(as_text=True)

            # The template shows transaction count
            assert '8' in data

    def test_profile_shows_top_category(self, seeded_app):
        """Test that profile shows Shopping as top category."""
        with seeded_app.test_client() as client:
            client.post('/login', data={
                'email': 'demo@spendly.com',
                'password': 'demo123'
            }, follow_redirects=False)

            response = client.get('/profile')
            data = response.get_data(as_text=True)

            assert 'Shopping' in data

    def test_profile_empty_state_for_new_user(self, app):
        """Test that new user with no expenses sees empty state."""
        with app.app_context():
            db = get_db()
            # Create a new user with no expenses (with proper password hash)
            password_hash = generate_password_hash('password123')
            db.execute(
                'INSERT INTO users (name, email, password_hash) VALUES (?, ?, ?)',
                ('New User', 'newuser@example.com', password_hash)
            )
            db.commit()

        with app.test_client() as client:
            client.post('/login', data={
                'email': 'newuser@example.com',
                'password': 'password123'
            }, follow_redirects=False)

            response = client.get('/profile')
            data = response.get_data(as_text=True)

            assert response.status_code == 200
            assert 'New User' in data
            assert '0' in data  # Should show 0 spent or 0 transactions
