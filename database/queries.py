"""Query functions for Spendly expense tracker.

Provides helper functions for querying expense data,
including category breakdowns and spending analytics.
"""

from database.db import get_db


def get_user_by_id(user_id: int) -> dict | None:
    """Fetch user record by ID.

    Args:
        user_id: The ID of the user to fetch.

    Returns:
        dict with keys: name, email, member_since (formatted "Month YYYY").
        None if user not found.

    Example:
        {"name": "Demo User", "email": "demo@spendly.com", "member_since": "April 2025"}
    """
    db = get_db()

    user = db.execute(
        """
        SELECT id, name, email, created_at
        FROM users
        WHERE id = ?
        """,
        (user_id,)
    ).fetchone()

    if user is None:
        return None

    # Format created_at as "Month YYYY"
    from datetime import datetime
    created_at = user["created_at"]
    if isinstance(created_at, str):
        dt = datetime.fromisoformat(created_at.replace("Z", "+00:00").split("+")[0])
    else:
        dt = created_at

    member_since = dt.strftime("%B %Y")

    return {
        "name": user["name"],
        "email": user["email"],
        "member_since": member_since
    }


def get_recent_transactions(user_id: int, limit: int = 10) -> list:
    """Fetch recent transactions for a given user.

    Args:
        user_id: The ID of the user whose transactions to fetch.
        limit: Maximum number of transactions to return (default 10).

    Returns:
        list: List of dicts with keys: date, description, category, amount.
              Ordered by date DESC (newest first).
              Returns empty list if user has no expenses.

    Example:
        [
            {"date": "2025-04-12", "description": "Dinner", "category": "Food", "amount": 60.00},
            {"date": "2025-04-11", "description": "Misc items", "category": "Other", "amount": 25.00},
        ]
    """
    db = get_db()

    cursor = db.execute(
        """
        SELECT date, description, category, amount
        FROM expenses
        WHERE user_id = ?
        ORDER BY date DESC
        LIMIT ?
        """,
        (user_id, limit)
    )

    rows = cursor.fetchall()

    return [
        {
            "date": row["date"],
            "description": row["description"],
            "category": row["category"],
            "amount": row["amount"]
        }
        for row in rows
    ]


def get_category_breakdown(user_id: int) -> list:
    """Get spending breakdown by category for a user.

    Args:
        user_id: The ID of the user to get breakdown for.

    Returns:
        list: List of dicts with keys:
            - name: category name (str)
            - amount: total spent in that category (float)
            - percentage: int percentage of total spending (sums to 100)
        Returns empty list if user has no expenses.

    Example:
        [
            {"name": "Shopping", "amount": 150.00, "percentage": 26},
            {"name": "Transport", "amount": 120.00, "percentage": 21},
            {"name": "Food", "amount": 105.50, "percentage": 18},
            ...
        ]
    """
    db = get_db()

    # Get category totals ordered by amount DESC
    rows = db.execute('''
        SELECT category, SUM(amount) as total
        FROM expenses
        WHERE user_id = ?
        GROUP BY category
        ORDER BY total DESC
    ''', (user_id,)).fetchall()

    if not rows:
        return []

    # Calculate total spending
    total_spending = sum(row['total'] for row in rows)

    if total_spending == 0:
        return []

    # Calculate percentages as share of total spending
    breakdown = []
    running_total = 0

    for i, row in enumerate(rows):
        # Calculate percentage share
        percentage = round((row['total'] / total_spending) * 100)
        breakdown.append({
            'name': row['category'],
            'amount': row['total'],
            'percentage': percentage
        })
        running_total += percentage

    # Adjust for rounding errors to ensure sum is exactly 100
    # Add/subtract the difference from the largest category
    diff = 100 - running_total
    if diff != 0 and len(breakdown) > 0:
        breakdown[0]['percentage'] += diff

    return breakdown


def get_summary_stats(user_id: int) -> dict:
    """Get summary statistics for a user's expenses.

    Args:
        user_id: The ID of the user to get stats for.

    Returns:
        dict with keys:
            - total_spent: float - sum of all expense amounts
            - transaction_count: int - number of expenses
            - top_category: str - category with highest total spending

    Example:
        {"total_spent": 575.50, "transaction_count": 8, "top_category": "Shopping"}

    Edge case (no expenses):
        {"total_spent": 0.0, "transaction_count": 0, "top_category": "—"}
    """
    db = get_db()

    # Get total spent and transaction count
    stats = db.execute(
        '''
        SELECT
            COALESCE(SUM(amount), 0) AS total_spent,
            COUNT(*) AS transaction_count
        FROM expenses
        WHERE user_id = ?
        ''',
        (user_id,)
    ).fetchone()

    total_spent = float(stats['total_spent']) if stats['total_spent'] else 0.0
    transaction_count = stats['transaction_count'] if stats['transaction_count'] else 0

    # Handle edge case: no expenses
    if transaction_count == 0:
        return {
            'total_spent': 0.0,
            'transaction_count': 0,
            'top_category': '—'
        }

    # Get top category (category with highest total amount)
    top_category_result = db.execute(
        '''
        SELECT category, SUM(amount) AS category_total
        FROM expenses
        WHERE user_id = ?
        GROUP BY category
        ORDER BY category_total DESC
        LIMIT 1
        ''',
        (user_id,)
    ).fetchone()

    top_category = top_category_result['category'] if top_category_result else '—'

    return {
        'total_spent': total_spent,
        'transaction_count': transaction_count,
        'top_category': top_category
    }
