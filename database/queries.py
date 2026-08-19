from database.db import get_db


def _apply_date_filter(query, params, date_from, date_to):
    if date_from is not None and date_to is not None:
        query += " AND date BETWEEN ? AND ?"
        params.append(date_from)
        params.append(date_to)
    return query


def get_summary_stats(user_id, date_from=None, date_to=None):
    conn = get_db()

    totals_query = (
        "SELECT COUNT(*) AS transaction_count, COALESCE(SUM(amount), 0) AS total_spent "
        "FROM expenses WHERE user_id = ?"
    )
    totals_params = [user_id]
    totals_query = _apply_date_filter(totals_query, totals_params, date_from, date_to)
    totals_row = conn.execute(totals_query, totals_params).fetchone()

    top_category_query = "SELECT category, SUM(amount) AS total FROM expenses WHERE user_id = ?"
    top_category_params = [user_id]
    top_category_query = _apply_date_filter(top_category_query, top_category_params, date_from, date_to)
    top_category_query += " GROUP BY category ORDER BY total DESC LIMIT 1"
    top_category_row = conn.execute(top_category_query, top_category_params).fetchone()

    conn.close()
    return {
        "total_spent": totals_row["total_spent"],
        "transaction_count": totals_row["transaction_count"],
        "top_category": top_category_row["category"] if top_category_row else None,
        "top_category_total": top_category_row["total"] if top_category_row else None,
    }


def get_recent_transactions(user_id, limit=10, date_from=None, date_to=None):
    conn = get_db()
    query = "SELECT * FROM expenses WHERE user_id = ?"
    params = [user_id]
    query = _apply_date_filter(query, params, date_from, date_to)
    query += " ORDER BY date DESC, id DESC LIMIT ?"
    params.append(limit)
    rows = conn.execute(query, params).fetchall()
    conn.close()
    return rows


def get_category_breakdown(user_id, date_from=None, date_to=None):
    conn = get_db()
    query = "SELECT category, SUM(amount) AS total FROM expenses WHERE user_id = ?"
    params = [user_id]
    query = _apply_date_filter(query, params, date_from, date_to)
    query += " GROUP BY category ORDER BY total DESC"
    rows = conn.execute(query, params).fetchall()
    conn.close()
    return rows
