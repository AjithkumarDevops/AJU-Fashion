from flask import Flask, render_template, request, redirect, url_for, session
import sqlite3
from datetime import datetime
import os

app = Flask(__name__)

DATABASE = "orders.db"

# Admin credentials
ADMIN_USERNAME = os.environ.get("ADMIN_USERNAME", "Ajufashion")
ADMIN_PASSWORD = os.environ.get("ADMIN_PASSWORD", "Ajith@1221997")

# Session secret key
app.secret_key = os.environ.get(
    "SECRET_KEY",
    "aju-fashion-secret-key-change-later"
)


def init_db():
    conn = sqlite3.connect(DATABASE)

    conn.execute("""
        CREATE TABLE IF NOT EXISTS orders (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            customer_name TEXT NOT NULL,
            phone TEXT NOT NULL,
            address TEXT NOT NULL,
            products TEXT NOT NULL,
            total REAL NOT NULL,
            payment_method TEXT NOT NULL,
            status TEXT NOT NULL DEFAULT 'NEW',
            order_date TEXT NOT NULL
        )
    """)

    conn.commit()
    conn.close()


# =========================
# CUSTOMER HOME
# =========================

@app.route("/")
def home():
    return render_template("index.html")


# =========================
# HEALTH CHECK
# =========================

@app.route("/health")
def health():
    return {"status": "healthy"}


# =========================
# CUSTOMER CHECKOUT
# =========================

@app.route("/checkout", methods=["GET", "POST"])
def checkout():

    if request.method == "POST":

        customer_name = request.form["customer_name"]
        phone = request.form["phone"]
        address = request.form["address"]
        products = request.form["products"]
        total = request.form["total"]
        payment_method = request.form["payment_method"]

        conn = sqlite3.connect(DATABASE)

        conn.execute("""
            INSERT INTO orders
            (customer_name, phone, address, products, total,
             payment_method, status, order_date)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            customer_name,
            phone,
            address,
            products,
            total,
            payment_method,
            "NEW",
            datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        ))

        conn.commit()

        order_id = conn.execute(
            "SELECT last_insert_rowid()"
        ).fetchone()[0]

        conn.close()

        return render_template(
            "order_success.html",
            order_id=order_id
        )

    return "Checkout page"


# =========================
# CUSTOMER ORDER TRACKING
# =========================

@app.route("/track-order", methods=["GET", "POST"])
def track_order():

    order = None
    error = None

    if request.method == "POST":

        order_id = request.form["order_id"].strip()

        if not order_id.isdigit():
            error = "Please enter a valid Order ID."

        else:
            conn = sqlite3.connect(DATABASE)
            conn.row_factory = sqlite3.Row

            order = conn.execute(
                "SELECT * FROM orders WHERE id = ?",
                (int(order_id),)
            ).fetchone()

            conn.close()

            if order is None:
                error = "Order not found. Please check your Order ID."

    return render_template(
        "track_order.html",
        order=order,
        error=error
    )


# =========================
# ADMIN LOGIN
# =========================

@app.route("/admin/login", methods=["GET", "POST"])
def admin_login():

    if request.method == "POST":

        username = request.form["username"]
        password = request.form["password"]

        if (
            username == ADMIN_USERNAME
            and password == ADMIN_PASSWORD
        ):
            session["admin_logged_in"] = True

            return redirect(url_for("admin"))

        return render_template(
            "admin_login.html",
            error="Invalid username or password"
        )

    return render_template("admin_login.html")


# =========================
# ADMIN DASHBOARD
# =========================

@app.route("/admin")
def admin():

    if not session.get("admin_logged_in"):
        return redirect(url_for("admin_login"))

    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row

    orders = conn.execute(
        "SELECT * FROM orders ORDER BY id DESC"
    ).fetchall()

    conn.close()

    return render_template(
        "admin.html",
        orders=orders
    )


# =========================
# UPDATE ORDER STATUS
# =========================

@app.route("/admin/update/<int:order_id>/<status>")
def update_order(order_id, status):

    if not session.get("admin_logged_in"):
        return redirect(url_for("admin_login"))

    allowed_status = [
        "NEW",
        "CONFIRMED",
        "SHIPPED",
        "DELIVERED"
    ]

    if status not in allowed_status:
        return "Invalid order status", 400

    conn = sqlite3.connect(DATABASE)

    conn.execute(
        "UPDATE orders SET status = ? WHERE id = ?",
        (status, order_id)
    )

    conn.commit()
    conn.close()

    return redirect(url_for("admin"))


# =========================
# ADMIN LOGOUT
# =========================

@app.route("/admin/logout")
def admin_logout():

    session.clear()

    return redirect(url_for("admin_login"))


# =========================
# START APPLICATION
# =========================

if __name__ == "__main__":

    init_db()

    app.run(
        host="0.0.0.0",
        port=5000,
        debug=True
    )