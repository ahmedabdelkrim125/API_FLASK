from app import create_app
from models import db, User, Booking, Payment, Field
from datetime import date, time

app = create_app()

with app.app_context():
    # Get or create the test user
    user = User.query.filter_by(email="test@example.com").first()
    if not user:
        user = User(
            name="Test User",
            email="test@example.com",
            role="user"
        )
        user.set_password("newpassword123")
        db.session.add(user)
        db.session.commit()
        print("Created test user")
    else:
        print(f"Found user: {user.name}")
        
    # Create a test field first
    field = Field.query.first()
    if not field:
        field = Field(
            name="Test Field",
            location="Test Location",
            governorate="cairo",
            price_per_hour=250.0,
            description="Test field for payments",
            owner_id=user.id  # Set the owner to the test user
        )
        db.session.add(field)
        db.session.commit()
        print("Created test field")
    else:
        print("Using existing field")
    
    # Create a test booking
    booking = Booking(
        user_id=user.id,
        field_id=field.id,
        date=date(2025, 12, 25),
        start_time=time(10, 0, 0),
        end_time=time(12, 0, 0),
        total_price=500.0,
        status="confirmed"
    )
    
    db.session.add(booking)
    db.session.commit()
    print("Created test booking")
    
    # Create a test payment
    payment = Payment(
        booking_id=booking.id,
        user_id=user.id,
        amount=500.0,
        currency="EGP",
        payment_method="vodafone_cash"
    )
    payment.status = "completed"
    payment.transaction_id = f"txn_{payment.id}_123456789"
    
    db.session.add(payment)
    db.session.commit()
    print(f"Created payment: {payment.to_dict()}")
    
    # Fetch and display payment info
    fetched_payment = Payment.query.get(payment.id)
    print(f"Payment info: {fetched_payment.to_dict()}")