from flask import Flask, render_template

from dash import db, widgets

app = Flask(__name__)


@app.get("/")
def overview():
    return render_template("overview.html", widgets=[w() for w in widgets.ALL])


@app.get("/orders")
def orders():
    rows = db.query("SELECT * FROM orders ORDER BY created_at DESC")
    return render_template("orders.html", orders=rows)


@app.get("/reports")
def reports():
    months = db.query("SELECT DISTINCT month FROM sales ORDER BY month DESC")
    return render_template("reports.html", months=months)


@app.get("/settings")
def settings():
    return render_template("settings.html")
