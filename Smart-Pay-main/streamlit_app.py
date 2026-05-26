import json
import streamlit as st
import pandas as pd
from datetime import datetime

from database import engine, SessionLocal, Base
from models import User, Transaction
from risk_engine import calculate_risk
from aml_engine import check_aml
from fraud_model import train_fraud_model

Base.metadata.create_all(bind=engine)

try:
    cache_resource = st.cache_resource
except AttributeError:
    cache_resource = st.cache_data

@cache_resource
def load_model():
    return train_fraud_model()

@cache_resource
def load_transactions():
    session = SessionLocal()
    try:
        txns = session.query(Transaction).order_by(Transaction.timestamp).all()
        return txns
    finally:
        session.close()

@cache_resource
def load_users():
    session = SessionLocal()
    try:
        return session.query(User).all()
    finally:
        session.close()


def create_sample_data():
    session = SessionLocal()
    try:
        # Create sample users only if no existing users exist
        if not session.query(User).count():
            alice = User(
                name="Alice",
                email="alice@test.com",
                mobile="9001001000",
                wallet_balance=50000.0,
                kyc_status="Verified",
                risk_score=5,
            )
            bob = User(
                name="Bob",
                email="bob@test.com",
                mobile="9002002000",
                wallet_balance=30000.0,
                kyc_status="Verified",
                risk_score=10,
            )
            charlie = User(
                name="Charlie",
                email="charlie@test.com",
                mobile="9003003000",
                wallet_balance=100000.0,
                kyc_status="Verified",
                risk_score=15,
            )
            session.add_all([alice, bob, charlie])
            session.commit()
        else:
            alice, bob, charlie = session.query(User).order_by(User.id).limit(3).all()

        if not session.query(Transaction).count():
            txns = [
                Transaction(sender_id=alice.id, receiver_id=bob.id, amount=5000.0, txn_type="P2P", country="India", fraud_flag=0, risk_score=15),
                Transaction(sender_id=alice.id, receiver_id=bob.id, amount=7000.0, txn_type="P2P", country="India", fraud_flag=0, risk_score=25),
                Transaction(sender_id=alice.id, receiver_id=bob.id, amount=9000.0, txn_type="P2P", country="India", fraud_flag=0, risk_score=35),
                Transaction(sender_id=bob.id, receiver_id=charlie.id, amount=15000.0, txn_type="P2P", country="USA", fraud_flag=0, risk_score=45),
                Transaction(sender_id=bob.id, receiver_id=charlie.id, amount=17000.0, txn_type="P2P", country="USA", fraud_flag=0, risk_score=55),
                Transaction(sender_id=bob.id, receiver_id=charlie.id, amount=19000.0, txn_type="P2P", country="USA", fraud_flag=1, risk_score=75),
                Transaction(sender_id=charlie.id, receiver_id=alice.id, amount=3000.0, txn_type="P2P", country="India", fraud_flag=0, risk_score=20),
                Transaction(sender_id=charlie.id, receiver_id=alice.id, amount=2500.0, txn_type="P2P", country="India", fraud_flag=0, risk_score=18),
            ]
            session.add_all(txns)
            session.commit()
        return True
    except Exception:
        session.rollback()
        return False
    finally:
        session.close()


st.set_page_config(page_title="SmartPay Dashboard", layout="wide")
st.title("SmartPay Streamlit Dashboard")
st.write("A Streamlit version of the SmartPay analytics dashboard.")

model = load_model()
users = load_users()
transactions = load_transactions()

if not users and not transactions:
    st.info("No data available yet. Use the sample forms below to create users and transactions.")

if st.button("Generate Sample Users and Transactions"):
    created = create_sample_data()
    if created:
        load_users.clear()
        load_transactions.clear()
        st.success("Sample users and transactions created. Reloading page...")
    else:
        st.error("Failed to create sample data. Try again.")

user_df = pd.DataFrame([
    {
        "ID": u.id,
        "Name": u.name,
        "Email": u.email,
        "Mobile": u.mobile,
        "Balance": u.wallet_balance,
        "KYC Status": u.kyc_status,
        "Risk Score": u.risk_score,
    }
    for u in users
]) if users else pd.DataFrame()

txn_df = pd.DataFrame([
    {
        "ID": t.id,
        "Sender": t.sender_id,
        "Receiver": t.receiver_id,
        "Amount": t.amount,
        "Type": t.txn_type,
        "Country": t.country,
        "Risk Score": t.risk_score,
        "Fraud Flag": t.fraud_flag,
        "Timestamp": t.timestamp,
    }
    for t in transactions
]) if transactions else pd.DataFrame()

col1, col2, col3 = st.columns(3)

with col1:
    st.metric("Total Transactions", len(txn_df))
with col2:
    st.metric("Fraud Transactions", int(txn_df["Fraud Flag"].sum() if not txn_df.empty else 0))
with col3:
    fraud_rate = (txn_df["Fraud Flag"].sum() / len(txn_df) * 100) if not txn_df.empty else 0
    st.metric("Fraud Rate", f"{fraud_rate:.2f}%")

if not txn_df.empty:
    chart_col1, chart_col2 = st.columns(2)
    with chart_col1:
        st.subheader("Risk Score by Transaction")
        risk_chart = txn_df[["Risk Score"]].copy()
        risk_chart.index = txn_df["Timestamp"].dt.strftime("%Y-%m-%d %H:%M:%S")
        st.bar_chart(risk_chart)

    with chart_col2:
        st.subheader("Transaction Amounts")
        amount_chart = txn_df[["Amount"]].copy()
        amount_chart.index = txn_df["Timestamp"].dt.strftime("%Y-%m-%d %H:%M:%S")
        st.line_chart(amount_chart)

st.markdown("---")

st.subheader("Users")
if user_df.empty:
    st.write("No users found.")
else:
    st.dataframe(user_df)

st.subheader("Transactions")
if txn_df.empty:
    st.write("No transactions found.")
else:
    st.dataframe(txn_df)

st.markdown("---")

st.subheader("Create a New Transaction")
with st.form("transaction_form"):
    sender_id = st.number_input("Sender user ID", min_value=1, step=1)
    receiver_id = st.number_input("Receiver user ID", min_value=1, step=1)
    amount = st.number_input("Amount", min_value=0.0, step=1.0, format="%.2f")
    device_change = st.checkbox("Device change detected")
    otp_failures = st.number_input("OTP failures", min_value=0, step=1)
    country = st.text_input("Country", value="India")
    submitted = st.form_submit_button("Submit Transaction")

if submitted:
    session = SessionLocal()
    try:
        sender = session.query(User).filter(User.id == sender_id).first()
        receiver = session.query(User).filter(User.id == receiver_id).first()
        if sender is None or receiver is None:
            st.error("Sender or receiver user ID not found.")
        elif sender.wallet_balance < amount:
            st.error("Sender has insufficient balance.")
        else:
            risk_score, risk_category = calculate_risk(amount, device_change, otp_failures)
            previous_txns = session.query(Transaction).filter(
                Transaction.sender_id == sender.id,
                Transaction.receiver_id == receiver.id,
            ).count()
            aml_flags = check_aml(amount, country, previous_txns)
            fraud_flag = 1 if aml_flags or model.predict([[amount, int(device_change), otp_failures]])[0] == 1 else 0

            sender.wallet_balance -= amount
            receiver.wallet_balance += amount
            sender.risk_score = risk_score
            receiver.risk_score = receiver.risk_score or 0

            txn = Transaction(
                sender_id=sender.id,
                receiver_id=receiver.id,
                amount=amount,
                txn_type="P2P",
                country=country,
                fraud_flag=fraud_flag,
                risk_score=risk_score,
                timestamp=datetime.utcnow(),
            )
            session.add(txn)
            session.commit()
            st.success("Transaction recorded successfully.")
            st.write({
                "risk_score": risk_score,
                "risk_category": risk_category,
                "aml_flags": aml_flags,
                "fraud_flag": fraud_flag,
            })
    finally:
        session.close()
