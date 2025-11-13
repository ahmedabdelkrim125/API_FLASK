import unittest
from app import create_app
from models import db, User, Booking, Payment, Field
from datetime import datetime, date, time

class PaymentUpdateTestCase(unittest.TestCase):
    def setUp(self):
        """Set up test environment"""
        self.app = create_app()
        self.app.config['TESTING'] = True
        self.app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'
        self.client = self.app.test_client()
        
        with self.app.app_context():
            db.create_all()
            
            # Create test user
            user = User(name='Test User', email='test@example.com', password='password123', role='user')
            db.session.add(user)
            db.session.commit()
            self.user_id = user.id
            
            # Create test field
            field = Field(
                name='Test Field',
                location='Test Location',
                governorate='Cairo',
                price_per_hour=100.0,
                owner_id=user.id
            )
            db.session.add(field)
            db.session.commit()
            self.field_id = field.id
            
            # Create test booking
            booking = Booking(
                user_id=self.user_id,
                field_id=self.field_id,
                date=date(2025, 12, 25),
                start_time=time(10, 0),
                end_time=time(12, 0),
                total_price=200.0
            )
            db.session.add(booking)
            db.session.commit()
            self.booking_id = booking.id

    def tearDown(self):
        """Clean up after tests"""
        with self.app.app_context():
            db.session.remove()
            db.drop_all()

    def test_payment_refund(self):
        """Test payment refund functionality"""
        with self.app.app_context():
            # Create a payment
            payment = Payment(
                booking_id=self.booking_id,
                user_id=self.user_id,
                amount=200.0,
                currency='EGP',
                payment_method='vodafone_cash'
            )
            payment.status = 'completed'  # Set status after initialization
            db.session.add(payment)
            db.session.commit()
            payment_id = payment.id
            
            # Verify payment status is completed
            payment = Payment.query.get(payment_id)
            self.assertEqual(payment.status, 'completed')
            
            # Refund the payment
            payment.status = 'refunded'
            payment.completed_at = datetime.utcnow()
            db.session.commit()
            
            # Verify payment status is refunded
            payment = Payment.query.get(payment_id)
            self.assertEqual(payment.status, 'refunded')
            self.assertIsNotNone(payment.completed_at)

    def test_payment_status_update(self):
        """Test payment status update functionality"""
        with self.app.app_context():
            # Create a payment
            payment = Payment(
                booking_id=self.booking_id,
                user_id=self.user_id,
                amount=200.0,
                currency='EGP',
                payment_method='vodafone_cash'
            )
            payment.status = 'pending'  # Set status after initialization
            db.session.add(payment)
            db.session.commit()
            payment_id = payment.id
            
            # Verify payment status is pending
            payment = Payment.query.get(payment_id)
            self.assertEqual(payment.status, 'pending')
            
            # Update payment status to completed
            payment.status = 'completed'
            payment.completed_at = datetime.utcnow()
            payment.transaction_id = f"txn_{payment.id}_{int(datetime.utcnow().timestamp())}"
            db.session.commit()
            
            # Verify payment status is completed
            payment = Payment.query.get(payment_id)
            self.assertEqual(payment.status, 'completed')
            self.assertIsNotNone(payment.completed_at)
            self.assertIsNotNone(payment.transaction_id)

if __name__ == '__main__':
    unittest.main()