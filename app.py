from flask import Flask, jsonify, render_template, request, redirect, url_for, session
import sqlite3
import pickle
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime
from email_utils import send_fraud_email, get_user_email

app = Flask(__name__)
app.secret_key = "supersecretkey"

def get_db():
    return sqlite3.connect("customers.db")

# Train ML model
with open("fraud_model.pkl", "rb") as f:
    model = pickle.load(f)
    

# Database connection
def get_db():
    return sqlite3.connect("customers.db")

# REGISTER 
@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        customer_id = request.form["customer_id"]
        email = request.form["email"]
        phone = request.form["phone"]
        password = generate_password_hash(request.form["password"])

        try:
            conn = get_db()
            cursor = conn.cursor()
            cursor.execute(
                "INSERT INTO customers (customer_id, email, phone, password) VALUES (?,?,?,?)",
                (customer_id, email, phone, password)
            )
            conn.commit()
            conn.close()
            return redirect(url_for("login"))
        except Exception as e:
            return "⚠️ Customer ID or Phone already exists"

    return render_template("register.html")


# LOGIN 
@app.route("/", methods=["GET", "POST"])
@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        customer_id = request.form["customer_id"]
        password = request.form["password"]

        conn = get_db()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM customers WHERE customer_id=?", (customer_id,))
        customer = cursor.fetchone()
        conn.close()

        if customer and check_password_hash(customer[4], password):
            session["customer"] = customer_id

            return redirect(url_for("dashboard"))
        else:
            return "❌ Invalid Credentials"

    return render_template("login.html")


# DASHBOARD 
@app.route("/dashboard", methods=["GET", "POST"])
def dashboard():
    if "customer" not in session:
        return redirect(url_for("login"))

    result = None
    txn_datetime = None  

    if request.method == "POST":
        amount = float(request.form["amount"])
        prediction = model.predict([[amount]])

        date_input = request.form["txn_date"]  
        time_input = request.form["txn_time"]  

        # Convert to datetime object
        try:
            dt_obj = datetime.strptime(f"{date_input} {time_input}", "%Y-%m-%d %H:%M")
            # Format as dd/mm/yy hh:mm
            txn_datetime = dt_obj.strftime("%d/%m/%y %H:%M")
        except:
            txn_datetime = f"{date_input} {time_input}"  

        if prediction[0] == -1:
            result = "🚨 FRAUD TRANSACTION"
            customer_id = session["customer"]
            user_email = get_user_email(customer_id)

            send_fraud_email(
            user_email,
            amount,
            txn_datetime
            )
        else:
            result = "✅ VALID TRANSACTION"

    return render_template(
        "dashboard.html",
        result=result,
        txn_datetime=txn_datetime
    )

@app.route("/predict", methods=["POST"])
def predict():
    data = request.json
    amount = data["amount"]
    user_email = data["email"]

    scaled_amount = scaler.transform([[amount]])
    prediction = model.predict(scaled_amount)

    if prediction[0] == 1: 
        send_fraud_alert(user_email, amount)
        return jsonify({
            "status": "fraud",
            "message": "🚨 Fraud detected! Email alert sent."
        })

    return jsonify({
        "status": "safe",
        "message": "✅ Transaction is safe"
    })

@app.route("/logout")
def logout():
    session.pop("user", None)
    return redirect(url_for("login"))

if __name__ == "__main__":
    app.run(debug=True)