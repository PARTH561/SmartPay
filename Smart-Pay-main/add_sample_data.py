"""
Script to add sample users and transactions to the database
Run this once: python add_sample_data.py
"""

from database import SessionLocal, engine, Base
from models import User, Transaction
from datetime import datetime, timedelta

# Create all tables
Base.metadata.create_all(bind=engine)

session = SessionLocal()

try:
    # Clear existing data (optional)
    session.query(Transaction).delete()
    session.query(User).delete()
    session.commit()
    
    # Create sample users
    alice = User(
        name="Alice",
        email="alice@test.com",
        mobile="9001001000",
        wallet_balance=50000.0,
        kyc_status="Verified",
        risk_score=5
    )
    
    bob = User(
        name="Bob",
        email="bob@test.com",
        mobile="9002002000",
        wallet_balance=30000.0,
        kyc_status="Verified",
        risk_score=10
    )
    
    charlie = User(
        name="Charlie",
        email="charlie@test.com",
        mobile="9003003000",
        wallet_balance=100000.0,
        kyc_status="Verified",
        risk_score=15
    )
    
    session.add_all([alice, bob, charlie])
    session.commit()
    
    print("✓ Users created: Alice, Bob, Charlie")
    
    # Refresh to get IDs
    session.refresh(alice)
    session.refresh(bob)
    session.refresh(charlie)
    
    # Create sample transactions
    txn1 = Transaction(
        sender_id=alice.id,
        receiver_id=bob.id,
        amount=5000.0,
        txn_type="Transfer",
        country="India",
        fraud_flag=0,
        risk_score=15,
        timestamp=datetime.utcnow() - timedelta(hours=3)
    )
    
    txn2 = Transaction(
        sender_id=alice.id,
        receiver_id=bob.id,
        amount=7000.0,
        txn_type="Transfer",
        country="India",
        fraud_flag=0,
        risk_score=25,
        timestamp=datetime.utcnow() - timedelta(hours=2)
    )
    
    txn3 = Transaction(
        sender_id=alice.id,
        receiver_id=bob.id,
        amount=9000.0,
        txn_type="Transfer",
        country="India",
        fraud_flag=0,
        risk_score=35,
        timestamp=datetime.utcnow() - timedelta(hours=1)
    )
    
    txn4 = Transaction(
        sender_id=bob.id,
        receiver_id=charlie.id,
        amount=15000.0,
        txn_type="Transfer",
        country="USA",
        fraud_flag=0,
        risk_score=45,
        timestamp=datetime.utcnow() - timedelta(minutes=30)
    )
    
    txn5 = Transaction(
        sender_id=bob.id,
        receiver_id=charlie.id,
        amount=17000.0,
        txn_type="Transfer",
        country="USA",
        fraud_flag=0,
        risk_score=55,
        timestamp=datetime.utcnow() - timedelta(minutes=20)
    )
    
    txn6 = Transaction(
        sender_id=bob.id,
        receiver_id=charlie.id,
        amount=19000.0,
        txn_type="Transfer",
        country="USA",
        fraud_flag=1,
        risk_score=75,
        timestamp=datetime.utcnow() - timedelta(minutes=10)
    )
    
    txn7 = Transaction(
        sender_id=charlie.id,
        receiver_id=alice.id,
        amount=3000.0,
        txn_type="Transfer",
        country="India",
        fraud_flag=0,
        risk_score=20,
        timestamp=datetime.utcnow() - timedelta(minutes=5)
    )
    
    txn8 = Transaction(
        sender_id=charlie.id,
        receiver_id=alice.id,
        amount=2500.0,
        txn_type="Transfer",
        country="India",
        fraud_flag=0,
        risk_score=18,
        timestamp=datetime.utcnow() - timedelta(minutes=1)
    )
    
    session.add_all([txn1, txn2, txn3, txn4, txn5, txn6, txn7, txn8])
    session.commit()
    
    print("✓ Transactions created: 8 transactions")
    print("\nData Summary:")
    print(f"  • Alice → Bob: 3 transactions (5k, 7k, 9k)")
    print(f"  • Bob → Charlie: 3 transactions (15k, 17k, 19k)")
    print(f"  • Charlie → Alice: 2 transactions (3k, 2.5k)")
    print(f"  • 1 flagged fraud transaction")
    
except Exception as e:
    session.rollback()
    print(f"Error: {e}")
    
finally:
    session.close()

print("\n✓ Sample data added successfully!")
print("Now run: python app.py")
