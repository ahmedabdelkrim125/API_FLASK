import unittest
from app import create_app
from models import db, User, Notification
from datetime import datetime

class NotificationsTestCase(unittest.TestCase):
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
            
            # Create test notifications
            notifications_data = [
                {'title': 'Booking Confirmation', 'message': 'Your booking has been confirmed', 'type': 'booking_confirmation'},
                {'title': 'Payment Successful', 'message': 'Your payment was processed', 'type': 'payment_success'},
                {'title': 'New Review', 'message': 'You received a new review', 'type': 'new_review'}
            ]
            
            for notif_data in notifications_data:
                notification = Notification(
                    user_id=self.user_id,
                    title=notif_data['title'],
                    message=notif_data['message'],
                    type=notif_data['type']
                )
                db.session.add(notification)
            
            db.session.commit()

    def tearDown(self):
        """Clean up after tests"""
        with self.app.app_context():
            db.session.remove()
            db.drop_all()

    def test_create_notification(self):
        """Test creating a notification"""
        with self.app.app_context():
            notification = Notification(
                user_id=self.user_id,
                title='Test Notification',
                message='This is a test notification',
                type='test'
            )
            db.session.add(notification)
            db.session.commit()
            
            # Verify notification was created
            retrieved_notification = Notification.query.get(notification.id)
            self.assertIsNotNone(retrieved_notification)
            self.assertEqual(retrieved_notification.title, 'Test Notification')
            self.assertEqual(retrieved_notification.message, 'This is a test notification')
            self.assertEqual(retrieved_notification.type, 'test')
            self.assertFalse(retrieved_notification.is_read)

    def test_mark_notification_as_read(self):
        """Test marking a notification as read"""
        with self.app.app_context():
            # Get first notification
            notification = Notification.query.first()
            self.assertFalse(notification.is_read)
            
            # Mark as read
            notification.is_read = True
            db.session.commit()
            
            # Verify it's marked as read
            updated_notification = Notification.query.get(notification.id)
            self.assertTrue(updated_notification.is_read)

    def test_get_user_notifications(self):
        """Test getting user notifications"""
        with self.app.app_context():
            # Get all notifications for user
            notifications = Notification.query.filter_by(user_id=self.user_id).all()
            
            # Should have 3 notifications
            self.assertEqual(len(notifications), 3)
            
            # All should belong to the test user
            for notification in notifications:
                self.assertEqual(notification.user_id, self.user_id)

    def test_filter_notifications_by_type(self):
        """Test filtering notifications by type"""
        with self.app.app_context():
            # Get booking confirmation notifications
            booking_notifications = Notification.query.filter_by(
                user_id=self.user_id,
                type='booking_confirmation'
            ).all()
            
            # Should have 1 booking confirmation
            self.assertEqual(len(booking_notifications), 1)
            self.assertEqual(booking_notifications[0].type, 'booking_confirmation')

    def test_get_unread_notifications_count(self):
        """Test getting unread notifications count"""
        with self.app.app_context():
            # Initially all notifications should be unread
            unread_count = Notification.query.filter_by(
                user_id=self.user_id,
                is_read=False
            ).count()
            
            # Should have 3 unread notifications
            self.assertEqual(unread_count, 3)
            
            # Mark one as read
            notification = Notification.query.first()
            notification.is_read = True
            db.session.commit()
            
            # Now should have 2 unread notifications
            unread_count = Notification.query.filter_by(
                user_id=self.user_id,
                is_read=False
            ).count()
            
            self.assertEqual(unread_count, 2)

if __name__ == '__main__':
    unittest.main()