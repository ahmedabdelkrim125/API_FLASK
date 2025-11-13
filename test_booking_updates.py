import unittest
from models import db, User, Field, Booking
from datetime import datetime, date, time
from flask import Flask
from flask_sqlalchemy import SQLAlchemy

class BookingUpdateTestCase(unittest.TestCase):
    def setUp(self):
        """Set up test environment"""
        self.app = Flask(__name__)
        self.app.config['TESTING'] = True
        self.app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'
        self.app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
        
        db.init_app(self.app)
        
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

    def tearDown(self):
        """Clean up after tests"""
        with self.app.app_context():
            db.session.remove()
            db.drop_all()

    def test_booking_cancellation(self):
        """Test booking cancellation functionality"""
        with self.app.app_context():
            # Create a booking
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
            booking_id = booking.id
            
            # Verify booking status is confirmed
            booking = Booking.query.get(booking_id)
            self.assertEqual(booking.status, 'confirmed')
            
            # Cancel the booking
            booking.status = 'cancelled'
            db.session.commit()
            
            # Verify booking status is cancelled
            booking = Booking.query.get(booking_id)
            self.assertEqual(booking.status, 'cancelled')

    def test_booking_update(self):
        """Test booking update functionality"""
        with self.app.app_context():
            # Create a booking
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
            booking_id = booking.id
            
            # Update booking time
            booking.date = date(2025, 12, 26)
            booking.start_time = time(14, 0)
            booking.end_time = time(16, 0)
            
            # Recalculate price
            field = Field.query.get(self.field_id)
            start_datetime = datetime.combine(booking.date, booking.start_time)
            end_datetime = datetime.combine(booking.date, booking.end_time)
            duration = (end_datetime - start_datetime).seconds / 3600
            booking.total_price = round(duration * field.price_per_hour, 2)
            
            db.session.commit()
            
            # Verify booking was updated
            booking = Booking.query.get(booking_id)
            self.assertEqual(booking.date, date(2025, 12, 26))
            self.assertEqual(booking.start_time, time(14, 0))
            self.assertEqual(booking.end_time, time(16, 0))
            self.assertEqual(booking.total_price, 200.0)  # 2 hours * 100 EGP/hour

if __name__ == '__main__':
    unittest.main()