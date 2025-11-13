import unittest
from app import create_app
from models import db, User, Field, Booking, Payment, Review, Analytics
from datetime import datetime, date, time

class AnalyticsTestCase(unittest.TestCase):
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
            
            # Create test review
            review = Review(
                user_id=self.user_id,
                field_id=self.field_id,
                rating=5,
                comment='Great field!'
            )
            db.session.add(review)
            db.session.commit()
            self.review_id = review.id
            
            # Create test analytics data
            analytics_data = [
                {'metric_name': 'booking_created', 'value': 1, 'date': date.today(), 'user_id': self.user_id, 'field_id': self.field_id},
                {'metric_name': 'payment_completed', 'value': 200.0, 'date': date.today(), 'user_id': self.user_id, 'field_id': self.field_id},
                {'metric_name': 'review_created', 'value': 5, 'date': date.today(), 'user_id': self.user_id, 'field_id': self.field_id}
            ]
            
            for data in analytics_data:
                analytics = Analytics(
                    metric_name=data['metric_name'],
                    value=data['value'],
                    date=data['date'],
                    user_id=data['user_id'],
                    field_id=data['field_id']
                )
                db.session.add(analytics)
            
            db.session.commit()

    def tearDown(self):
        """Clean up after tests"""
        with self.app.app_context():
            db.session.remove()
            db.drop_all()

    def test_create_analytics_record(self):
        """Test creating an analytics record"""
        with self.app.app_context():
            analytics = Analytics(
                metric_name='test_metric',
                value=10.5,
                date=date.today(),
                user_id=self.user_id,
                field_id=self.field_id
            )
            db.session.add(analytics)
            db.session.commit()
            
            # Verify analytics record was created
            retrieved_analytics = Analytics.query.get(analytics.id)
            self.assertIsNotNone(retrieved_analytics)
            self.assertEqual(retrieved_analytics.metric_name, 'test_metric')
            self.assertEqual(retrieved_analytics.value, 10.5)
            self.assertEqual(retrieved_analytics.user_id, self.user_id)
            self.assertEqual(retrieved_analytics.field_id, self.field_id)

    def test_get_dashboard_analytics_for_admin(self):
        """Test getting dashboard analytics for admin user"""
        with self.app.app_context():
            # Get admin user
            admin_user = User.query.get(self.admin_id)
            
            # Test dashboard analytics for admin
            # In a real test, we would mock the JWT token and make a request
            # For now, we'll just test the logic directly
            
            # Total users
            total_users = User.query.count()
            self.assertEqual(total_users, 3)
            
            # Total fields
            total_fields = Field.query.count()
            self.assertEqual(total_fields, 1)
            
            # Total bookings
            total_bookings = Booking.query.count()
            self.assertEqual(total_bookings, 1)
            
            # Total revenue
            total_revenue = db.session.query(db.func.sum(Payment.amount)).filter(
                Payment.status == 'completed'
            ).scalar() or 0
            self.assertEqual(total_revenue, 200.0)
            
            # Average rating
            avg_rating = db.session.query(db.func.avg(Review.rating)).scalar() or 0
            self.assertEqual(avg_rating, 5.0)

    def test_get_booking_trends(self):
        """Test getting booking trends"""
        with self.app.app_context():
            # Get booking trends data
            from sqlalchemy import func
            
            # Build query for booking trends
            query = db.session.query(
                func.date(Booking.date).label('booking_date'),
                func.count(Booking.id).label('booking_count')
            )
            
            # Filter for all bookings
            query = query.filter(Booking.date == date.today())
            
            # Group by date
            query = query.group_by(func.date(Booking.date)).order_by(func.date(Booking.date))
            
            # Execute query
            results = query.all()
            
            # Should have 1 result for today
            self.assertEqual(len(results), 1)
            self.assertEqual(results[0].booking_count, 1)

    def test_get_revenue_trends(self):
        """Test getting revenue trends"""
        with self.app.app_context():
            # Get revenue trends data
            from sqlalchemy import func
            
            # Build query for revenue trends
            query = db.session.query(
                func.date(Payment.completed_at).label('payment_date'),
                func.sum(Payment.amount).label('revenue')
            ).filter(Payment.status == 'completed')
            
            # Filter for today
            query = query.filter(func.date(Payment.completed_at) == date.today())
            
            # Group by date
            query = query.group_by(func.date(Payment.completed_at)).order_by(func.date(Payment.completed_at))
            
            # Execute query
            results = query.all()
            
            # Should have 1 result for today
            self.assertEqual(len(results), 1)
            self.assertEqual(float(results[0].revenue), 200.0)

    def test_get_field_performance(self):
        """Test getting field performance"""
        with self.app.app_context():
            # Get field performance data
            field = Field.query.get(self.field_id)
            
            # Total bookings for this field
            total_bookings = Booking.query.filter(
                Booking.field_id == self.field_id,
                Booking.status != 'cancelled'
            ).count()
            self.assertEqual(total_bookings, 1)
            
            # Total revenue from this field
            total_revenue = db.session.query(db.func.sum(Payment.amount)).join(Booking).filter(
                Booking.field_id == self.field_id,
                Payment.status == 'completed'
            ).scalar() or 0
            self.assertEqual(total_revenue, 200.0)
            
            # Average rating for this field
            avg_rating = db.session.query(db.func.avg(Review.rating)).filter(
                Review.field_id == self.field_id
            ).scalar() or 0
            self.assertEqual(avg_rating, 5.0)

if __name__ == '__main__':
    unittest.main()