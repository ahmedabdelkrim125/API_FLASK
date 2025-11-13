import unittest
from app import create_app
from models import db, User, Field
from datetime import datetime, date, time

class PaginationTestCase(unittest.TestCase):
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
            
            # Create multiple test fields to test pagination
            for i in range(15):
                field = Field(
                    name=f'Test Field {i+1}',
                    location=f'Test Location {i+1}',
                    governorate='Cairo',
                    price_per_hour=100.0,
                    owner_id=user.id
                )
                db.session.add(field)
            
            db.session.commit()

    def tearDown(self):
        """Clean up after tests"""
        with self.app.app_context():
            db.session.remove()
            db.drop_all()

    def test_fields_pagination(self):
        """Test pagination for fields endpoint"""
        with self.app.app_context():
            # Test default pagination (page=1, per_page=10)
            paginated_fields = Field.query.paginate(page=1, per_page=10, error_out=False)
            
            # Should have 10 items on first page
            self.assertEqual(len(paginated_fields.items), 10)
            
            # Should have 2 pages total (15 items, 10 per page)
            self.assertEqual(paginated_fields.pages, 2)
            
            # Should have next page
            self.assertTrue(paginated_fields.has_next)
            
            # Should not have previous page
            self.assertFalse(paginated_fields.has_prev)
            
            # Test second page
            paginated_fields_page_2 = Field.query.paginate(page=2, per_page=10, error_out=False)
            
            # Should have 5 items on second page
            self.assertEqual(len(paginated_fields_page_2.items), 5)
            
            # Should not have next page
            self.assertFalse(paginated_fields_page_2.has_next)
            
            # Should have previous page
            self.assertTrue(paginated_fields_page_2.has_prev)

    def test_pagination_parameters_validation(self):
        """Test pagination parameters validation"""
        with self.app.app_context():
            # Test page < 1 defaults to page 1
            paginated_fields = Field.query.paginate(page=0, per_page=10, error_out=False)
            self.assertEqual(paginated_fields.page, 1)
            
            # Test per_page < 1 defaults to 10
            paginated_fields = Field.query.paginate(page=1, per_page=0, error_out=False)
            self.assertEqual(paginated_fields.per_page, 10)
            
            # Test per_page > 100 defaults to 10
            paginated_fields = Field.query.paginate(page=1, per_page=150, error_out=False)
            self.assertEqual(paginated_fields.per_page, 10)

if __name__ == '__main__':
    unittest.main()