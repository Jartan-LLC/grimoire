from dash import db


def revenue_today():
    return db.query("SELECT sum(total) FROM orders WHERE created_at::date = current_date")


def top_customers():
    return db.query(
        "SELECT customer, sum(total) AS t FROM orders GROUP BY customer ORDER BY t DESC LIMIT 10"
    )


def pipeline():
    return db.query("SELECT stage, count(*) FROM deals GROUP BY stage")


def quota():
    return db.query(
        "SELECT rep, sum(total) FROM orders"
        " WHERE created_at > date_trunc('quarter', now()) GROUP BY rep"
    )


ALL = [revenue_today, top_customers, pipeline, quota]
