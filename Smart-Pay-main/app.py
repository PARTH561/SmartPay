from flask import Flask, request, jsonify
from database import engine, SessionLocal, Base
from models import User, Transaction
from datetime import datetime
from risk_engine import calculate_risk
from aml_engine import check_aml
from fraud_model import train_fraud_model
import json

fraud_model = train_fraud_model()

# Create tables
Base.metadata.create_all(bind=engine)

app = Flask(__name__)

@app.route("/")
def home():
    session = SessionLocal()
    txns = session.query(Transaction).all()

    total_txns = len(txns)
    total_fraud = sum(t.fraud_flag for t in txns)
    fraud_rate = (total_fraud / total_txns * 100) if total_txns else 0
    fraud_rate_str = f"{fraud_rate:.2f}"
    risk_scores = [t.risk_score for t in txns]
    amounts = [t.amount for t in txns]

    session.close()

    html_content = """
        <!doctype html>
        <html lang="en">
        <head>
          <meta charset="utf-8">
          <meta name="viewport" content="width=device-width, initial-scale=1">
          <title>SmartPay Analytics Dashboard</title>
          <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
          <style>
            body { font-family: Arial, sans-serif; margin: 0; padding: 0; background: #f4f7fb; }
            .container { max-width: 1000px; margin: 32px auto; padding: 16px; }
            .card { background: white; border-radius: 12px; padding: 20px; box-shadow: 0 12px 30px rgba(0,0,0,0.08); margin-bottom: 24px; }
            .row { display: grid; grid-template-columns: repeat(auto-fit, minmax(220px, 1fr)); gap: 16px; }
            .metric { font-size: 18px; margin: 8px 0; }
            h1, h2 { margin: 0 0 16px; }
          </style>
        </head>
        <body>
          <div class="container">
            <div class="card">
              <h1>SmartPay Analytics Dashboard</h1>
              <p>Live analytics from the payments database.</p>
            </div>

            <div class="row">
              <div class="card">
                <h2>Key Metrics</h2>
                <div class="metric">Total Transactions: <strong>%s</strong></div>
                <div class="metric">Fraud Transactions: <strong>%s</strong></div>
                <div class="metric">Fraud Rate: <strong>%s%%</strong></div>
              </div>
              <div class="card">
                <h2>Transaction Distribution</h2>
                <canvas id="riskChart" width="400" height="220"></canvas>
              </div>
            </div>

            <div class="card">
              <h2>Transaction Amounts</h2>
              <canvas id="amountChart" width="800" height="250"></canvas>
            </div>
          </div>

          <script>
            const riskData = %s;
            const amountData = %s;
            const labels = riskData.map((_, index) => `Txn ${index + 1}`);

            new Chart(document.getElementById('riskChart'), {
              type: 'bar',
              data: {
                labels: labels,
                datasets: [{
                  label: 'Risk Score',
                  data: riskData,
                  backgroundColor: 'rgba(255, 99, 132, 0.6)',
                  borderColor: 'rgba(255, 99, 132, 1)',
                  borderWidth: 1
                }]
              },
              options: { responsive: true, maintainAspectRatio: false, animation: false }
            });

            new Chart(document.getElementById('amountChart'), {
              type: 'line',
              data: {
                labels: labels,
                datasets: [{
                  label: 'Transaction Amount',
                  data: amountData,
                  fill: false,
                  borderColor: 'rgba(54, 162, 235, 1)',
                  tension: 0.3
                }]
              },
              options: { responsive: true, maintainAspectRatio: false, animation: false }
            });
          </script>
        </body>
        </html>
        """ % (
            total_txns,
            total_fraud,
            fraud_rate_str,
            json.dumps(risk_scores),
            json.dumps(amounts),
        )

    return html_content

@app.route("/register", methods=["POST"])
def register():
    session = SessionLocal()
    data = request.json

    try:
        user = User(
            name=data["name"],
            email=data["email"],
            mobile=data["mobile"]
        )

        session.add(user)
        session.commit()

        return jsonify({"message": "User registered successfully"})

    except Exception as e:
        session.rollback()
        return jsonify({"error": str(e)})

    finally:
        session.close()




@app.route("/add_money", methods=["POST"])
def add_money():
    session = SessionLocal()
    data = request.json

    try:
        user = session.query(User).filter(User.id == data["user_id"]).first()

        if not user:
            return jsonify({"error": "User not found"})

        user.wallet_balance += float(data["amount"])
        session.commit()

        return jsonify({
            "message": "Money added successfully",
            "new_balance": user.wallet_balance
        })

    except Exception as e:
        session.rollback()
        return jsonify({"error": str(e)})

    finally:
        session.close()



@app.route("/balance/<int:user_id>", methods=["GET"])
def check_balance(user_id):
    session = SessionLocal()

    user = session.query(User).filter(User.id == user_id).first()

    if not user:
        return jsonify({"error": "User not found"})

    return jsonify({
        "user": user.name,
        "wallet_balance": user.wallet_balance
    })

@app.route('/users', methods=['GET'])
def get_users():
    session = SessionLocal()
    users = session.query(User).all()

    user_list = []

    for user in users:
        user_list.append({
            "id": user.id,
            "name": user.name,
            "email": user.email,
            "mobile": user.mobile,
            "wallet_balance": user.wallet_balance
        })

    session.close()
    return jsonify(user_list)


@app.route("/transfer", methods=["POST"])
def transfer():
    session = SessionLocal()
    data = request.json

    try:
        sender = session.query(User).filter(User.id == data["sender_id"]).first()
        receiver = session.query(User).filter(User.id == data["receiver_id"]).first()

        if not sender or not receiver:
            return jsonify({"error": "Invalid sender or receiver"})

        amount = float(data["amount"])

        if sender.wallet_balance < amount:
            return jsonify({"error": "Insufficient balance"})

        # -------- RISK ENGINE --------
        device_change = data.get("device_change", False)
        otp_failures = data.get("otp_failures", 0)

        risk_score, risk_category = calculate_risk(
            amount, device_change, otp_failures
        )

        # -------- FRAUD MODEL --------
        ml_input = [[amount, int(device_change), otp_failures]]
        ml_prediction = fraud_model.predict(ml_input)[0]
        ml_probability = fraud_model.predict_proba(ml_input)[0][1]


        # -------- AML ENGINE --------
        country = data.get("country", "India")

        previous_txns_count = session.query(Transaction).filter(
            Transaction.sender_id == sender.id,
            Transaction.receiver_id == receiver.id
        ).count()

        aml_flags = check_aml(amount, country, previous_txns_count)

        # If AML flags exist → mark fraud_flag = 1
        fraud_flag = 1 if (aml_flags or ml_prediction == 1) else 0

        # -------- PROCESS TRANSACTION --------
        sender.wallet_balance -= amount
        receiver.wallet_balance += amount

        txn = Transaction(
            sender_id=sender.id,
            receiver_id=receiver.id,
            amount=amount,
            txn_type="P2P",
            country=country,
            risk_score=risk_score,
            fraud_flag=fraud_flag
        )

        session.add(txn)
        session.commit()

        return jsonify({
            "message": "Transfer processed",
            "risk_score": risk_score,
            "risk_category": risk_category,
            "aml_flags": aml_flags,
            "ml_fraud_prediction": int(ml_prediction),
            "ml_fraud_probability": float(ml_probability),
            "fraud_flag": fraud_flag,
            "sender_balance": sender.wallet_balance
        })

    except Exception as e:
        session.rollback()
        return jsonify({"error": str(e)})

    finally:
        session.close()











if __name__ == "__main__":
    app.run(debug=True)
