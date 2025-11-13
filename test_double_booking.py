import unittest
from app import create_app
from models import db, User, Field, Booking
from datetime import datetime, date, time

class DoubleBookingTestCase(unittest.TestCase):
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

    def tearDown(self):
        """Clean up after tests"""
        with self.app.app_context():
            db.session.remove()
            db.drop_all()

    def test_double_booking_prevention(self):
        """Test that double booking is prevented"""
        with self.app.app_context():
            # Create first booking
            booking1 = Booking(
                user_id=self.user_id,
                field_id=self.field_id,
                date=date(2025, 12, 25),
                start_time=time(10, 0),
                end_time=time(12, 0),
                total_price=200.0
            )
            db.session.add(booking1)
            db.session.commit()
            
            # Try to create overlapping booking
            booking2 = Booking(
                user_id=self.user_id,
                field_id=self.field_id,
                date=date(2025, 12, 25),
                start_time=time(11, 0),  # Overlaps with booking1
                end_time=time(13, 0),
                total_price=200.0
            )
            
            # Check for overlapping bookings
            overlapping_booking = Booking.query.filter(
                Booking.field_id == booking2.field_id,
                Booking.date == booking2.date,
                Booking.start_time < booking2.end_time,
                Booking.end_time > booking2.start_time,
                Booking.status != 'cancelled'
            ).first()
            
            # Verify that overlapping booking is detected
            self.assertIsNotNone(overlapping_booking)
            self.assertEqual(overlapping_booking.id, booking1.id)

    def test_non_overlapping_bookings_allowed(self):
        """Test that non-overlapping bookings are allowed"""
        with self.app.app_context():
            # Create first booking
            booking1 = Booking(
                user_id=self.user_id,
                field_id=self.field_id,
                date=date(2025, 12, 25),
                start_time=time(10, 0),
                end_time=time(12, 0),
                total_price=200.0
            )
            db.session.add(booking1)
            db.session.commit()
            
            # Create non-overlapping booking (after first booking)
            booking2 = Booking(
                user_id=self.user_id,
                field_id=self.field_id,
                date=date(2025, 12, 25),
                start_time=time(12, 0),  # Starts exactly when first ends
                end_time=time(14, 0),
                total_price=200.0
            )
            db.session.add(booking2)
            db.session.commit()
            
            # Verify both bookings exist
            bookings = Booking.query.filter_by(field_id=self.field_id, date=date(2025, 12, 25)).all()
            self.assertEqual(len(bookings), 2)

if __name__ == '__main__':
    unittest.main()