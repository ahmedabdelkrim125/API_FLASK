import unittest
from app import create_app
from models import db, User, Field, Booking
from datetime import datetime, date, time

class FieldAvailabilityTestCase(unittest.TestCase):
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
            
            # Create test field with custom opening hours
            field = Field(
                name='Test Field',
                location='Test Location',
                governorate='Cairo',
                price_per_hour=100.0,
                owner_id=user.id,
                opening_time=time(9, 0),  # 9:00 AM
                closing_time=time(21, 0)  # 9:00 PM
            )
            db.session.add(field)
            db.session.commit()
            self.field_id = field.id

    def tearDown(self):
        """Clean up after tests"""
        with self.app.app_context():
            db.session.remove()
            db.drop_all()

    def test_field_opening_hours(self):
        """Test that field opening hours are properly set"""
        with self.app.app_context():
            field = Field.query.get(self.field_id)
            self.assertEqual(field.opening_time, time(9, 0))
            self.assertEqual(field.closing_time, time(21, 0))

    def test_available_slots_calculation(self):
        """Test calculation of available time slots"""
        with self.app.app_context():
            field = Field.query.get(self.field_id)
            
            # Create a booking from 10:00 to 12:00
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
            
            # Get all bookings for the field on that date
            bookings = Booking.query.filter(
                Booking.field_id == self.field_id,
                Booking.date == date(2025, 12, 25),
                Booking.status != 'cancelled'
            ).all()
            
            # Calculate available slots
            available_slots = calculate_available_slots_for_testing(bookings, date(2025, 12, 25), field)
            
            # Should have two available slots: 9:00-10:00 and 12:00-21:00
            self.assertEqual(len(available_slots), 2)
            self.assertEqual(available_slots[0]['start_time'], time(9, 0).isoformat())
            self.assertEqual(available_slots[0]['end_time'], time(10, 0).isoformat())
            self.assertEqual(available_slots[1]['start_time'], time(12, 0).isoformat())
            self.assertEqual(available_slots[1]['end_time'], time(21, 0).isoformat())

def calculate_available_slots_for_testing(bookings, date, field):
    """
    Calculate available time slots based on existing bookings and field opening hours.
    This is a simplified version of the function in routes/bookings.py for testing.
    """
    # Use field's opening and closing times, with defaults if not set
    opening_time = field.opening_time if field.opening_time else time(8, 0)  # Default 8:00 AM
    closing_time = field.closing_time if field.closing_time else time(22, 0)  # Default 10:00 PM
    
    # If no bookings, the entire day is available
    if not bookings:
        return [{
            'start_time': opening_time.isoformat(),
            'end_time': closing_time.isoformat()
        }]
    
    # Sort bookings by start time
    sorted_bookings = sorted(bookings, key=lambda x: x.start_time)
    
    available_slots = []
    
    # Check for available slot before first booking
    if sorted_bookings[0].start_time > opening_time:
        available_slots.append({
            'start_time': opening_time.isoformat(),
            'end_time': sorted_bookings[0].start_time.isoformat()
        })
    
    # Check for available slots between bookings
    for i in range(len(sorted_bookings) - 1):
        current_booking = sorted_bookings[i]
        next_booking = sorted_bookings[i + 1]
        
        # If there's a gap between bookings
        if current_booking.end_time < next_booking.start_time:
            available_slots.append({
                'start_time': current_booking.end_time.isoformat(),
                'end_time': next_booking.start_time.isoformat()
            })
    
    # Check for available slot after last booking
    if sorted_bookings[-1].end_time < closing_time:
        available_slots.append({
            'start_time': sorted_bookings[-1].end_time.isoformat(),
            'end_time': closing_time.isoformat()
        })
    
    return available_slots

if __name__ == '__main__':
    unittest.main()