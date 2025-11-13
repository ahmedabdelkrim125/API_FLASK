import unittest
from app import create_app
from models import db, User, Field, Booking, Payment
from datetime import datetime, date, time
import csv
import io

class DataExportTestCase(unittest.TestCase):
    def setUp(self):
        """Set up test environment"""
        self.app = create_app()
        self.app.config['TESTING'] = True
        self.app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'
        self.client = self.app.test_client()
        
        with self.app.app_context():
            db.create_all()
            
            # Create test users
            admin_user = User(name='Admin User', email='admin@example.com', password='password123', role='admin')
            owner_user = User(name='Owner User', email='owner@example.com', password='password123', role='owner')
            regular_user = User(name='Regular User', email='user@example.com', password='password123', role='user')
            
            db.session.add(admin_user)
            db.session.add(owner_user)
            db.session.add(regular_user)
            db.session.commit()
            
            self.admin_id = admin_user.id
            self.owner_id = owner_user.id
            self.user_id = regular_user.id
            
            # Create test field
            field = Field(
                name='Test Field',
                location='Test Location',
                governorate='Cairo',
                price_per_hour=100.0,
                owner_id=self.owner_id
            )
            db.session.add(field)
            db.session.commit()
            self.field_id = field.id
            
            # Create test booking
            booking = Booking(
                user_id=self.user_id,
                field_id=self.field_id,
                date=date.today(),
                start_time=time(10, 0),
                end_time=time(12, 0),
                total_price=200.0,
                status='confirmed'
            )
            db.session.add(booking)
            db.session.commit()
            self.booking_id = booking.id
            
            # Create test payment
            payment = Payment(
                booking_id=self.booking_id,
                user_id=self.user_id,
                amount=200.0,
                payment_method='credit_card'
            )
            # Set additional fields
            payment.status = 'completed'
            payment.completed_at = datetime.utcnow()
            db.session.add(payment)
            db.session.commit()
            self.payment_id = payment.id

    def tearDown(self):
        """Clean up after tests"""
        with self.app.app_context():
            db.session.remove()
            db.drop_all()

    def test_csv_generation(self):
        """Test that CSV data can be generated correctly"""
        with self.app.app_context():
            # Test bookings data
            bookings = Booking.query.all()
            self.assertEqual(len(bookings), 1)
            
            # Create CSV data for bookings
            output = io.StringIO()
            writer = csv.writer(output)
            
            # Write header
            writer.writerow([
                'Booking ID', 'Date', 'Start Time', 'End Time', 
                'Total Price', 'Status', 'User Name', 'User Email', 'Field Name'
            ])
            
            # Write data
            for booking in bookings:
                user = User.query.get(booking.user_id)
                field = Field.query.get(booking.field_id)
                writer.writerow([
                    booking.id, booking.date, booking.start_time, booking.end_time,
                    booking.total_price, booking.status, user.name, user.email, field.name
                ])
            
            # Get CSV content
            csv_content = output.getvalue()
            output.close()
            
            # Verify CSV content
            self.assertIn('Booking ID', csv_content)
            self.assertIn('Test Field', csv_content)
            self.assertIn('Regular User', csv_content)
            
    def test_payment_csv_generation(self):
        """Test that payment CSV data can be generated correctly"""
        with self.app.app_context():
            # Test payments data
            payments = Payment.query.all()
            self.assertEqual(len(payments), 1)
            
            # Create CSV data for payments
            output = io.StringIO()
            writer = csv.writer(output)
            
            # Write header
            writer.writerow([
                'Payment ID', 'Amount', 'Currency', 'Payment Method', 
                'Status', 'Created At', 'Completed At', 'User Name', 'User Email', 'Field Name'
            ])
            
            # Write data
            for payment in payments:
                user = User.query.get(payment.user_id)
                booking = Booking.query.get(payment.booking_id)
                field = Field.query.get(booking.field_id)
                writer.writerow([
                    payment.id, payment.amount, payment.currency, payment.payment_method,
                    payment.status, payment.created_at, payment.completed_at, 
                    user.name, user.email, field.name
                ])
            
            # Get CSV content
            csv_content = output.getvalue()
            output.close()
            
            # Verify CSV content
            self.assertIn('Payment ID', csv_content)
            self.assertIn('200.0', csv_content)
            self.assertIn('Regular User', csv_content)

    def test_user_csv_generation(self):
        """Test that user CSV data can be generated correctly"""
        with self.app.app_context():
            # Test users data
            users = User.query.all()
            self.assertEqual(len(users), 3)
            
            # Create CSV data for users
            output = io.StringIO()
            writer = csv.writer(output)
            
            # Write header
            writer.writerow([
                'User ID', 'Name', 'Email', 'Role', 'Phone', 'Created At'
            ])
            
            # Write data
            for user in users:
                writer.writerow([
                    user.id, user.name, user.email, user.role, user.phone, user.created_at
                ])
            
            # Get CSV content
            csv_content = output.getvalue()
            output.close()
            
            # Verify CSV content
            self.assertIn('User ID', csv_content)
            self.assertIn('Admin User', csv_content)
            self.assertIn('Owner User', csv_content)
            self.assertIn('Regular User', csv_content)

if __name__ == '__main__':
    unittest.main()