import unittest
from app import create_app
from models import db, User, Field
from datetime import datetime, date, time

class AdvancedSearchTestCase(unittest.TestCase):
    def setUp(self):
        """Set up test environment"""
        self.app = create_app()
        self.app.config['TESTING'] = True
        self.app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'
        self.client = self.app.test_client()
        
        with self.app.app_context():
            db.create_all()
            
            # Create test user (field owner)
            owner = User(name='Test Owner', email='owner@example.com', password='password123', role='owner')
            db.session.add(owner)
            db.session.commit()
            
            # Create multiple test fields with different attributes
            fields_data = [
                {'name': 'Premium Field A', 'location': 'Downtown', 'governorate': 'Cairo', 'price_per_hour': 150.0},
                {'name': 'Standard Field B', 'location': 'Uptown', 'governorate': 'Giza', 'price_per_hour': 100.0},
                {'name': 'Economy Field C', 'location': 'Midtown', 'governorate': 'Cairo', 'price_per_hour': 75.0},
                {'name': 'Luxury Field D', 'location': 'Suburb', 'governorate': 'Alexandria', 'price_per_hour': 200.0},
                {'name': 'Basic Field E', 'location': 'Outskirts', 'governorate': 'Cairo', 'price_per_hour': 50.0}
            ]
            
            for field_data in fields_data:
                field = Field(
                    name=field_data['name'],
                    location=field_data['location'],
                    governorate=field_data['governorate'],
                    price_per_hour=field_data['price_per_hour'],
                    owner_id=owner.id
                )
                db.session.add(field)
            
            db.session.commit()

    def tearDown(self):
        """Clean up after tests"""
        with self.app.app_context():
            db.session.remove()
            db.drop_all()

    def test_fields_search_by_name(self):
        """Test searching fields by name"""
        with self.app.app_context():
            # Search for fields with 'Premium' in name
            query = Field.query.filter(Field.name.ilike('%Premium%'))
            fields = query.all()
            
            self.assertEqual(len(fields), 1)
            self.assertEqual(fields[0].name, 'Premium Field A')

    def test_fields_search_by_location(self):
        """Test searching fields by location"""
        with self.app.app_context():
            # Search for fields with 'town' in location
            query = Field.query.filter(Field.location.ilike('%town%'))
            fields = query.all()
            
            self.assertEqual(len(fields), 3)  # Downtown, Uptown, Midtown
            locations = [field.location for field in fields]
            self.assertIn('Downtown', locations)
            self.assertIn('Uptown', locations)
            self.assertIn('Midtown', locations)

    def test_fields_filter_by_governorate(self):
        """Test filtering fields by governorate"""
        with self.app.app_context():
            # Filter fields by governorate
            query = Field.query.filter_by(governorate='Cairo')
            fields = query.all()
            
            self.assertEqual(len(fields), 3)  # 3 fields in Cairo
            for field in fields:
                self.assertEqual(field.governorate, 'Cairo')

    def test_fields_filter_by_price_range(self):
        """Test filtering fields by price range"""
        with self.app.app_context():
            # Filter fields by price range (75-150)
            query = Field.query.filter(
                Field.price_per_hour >= 75,
                Field.price_per_hour <= 150
            )
            fields = query.all()
            
            self.assertEqual(len(fields), 3)  # Premium A (150), Standard B (100), Economy C (75)
            for field in fields:
                self.assertGreaterEqual(field.price_per_hour, 75)
                self.assertLessEqual(field.price_per_hour, 150)

    def test_fields_sorting(self):
        """Test sorting fields"""
        with self.app.app_context():
            # Sort fields by price ascending
            query = Field.query.order_by(Field.price_per_hour.asc())
            fields = query.all()
            
            prices = [field.price_per_hour for field in fields]
            self.assertEqual(prices, sorted(prices))  # Should be sorted
            
            # Sort fields by name descending
            query = Field.query.order_by(Field.name.desc())
            fields = query.all()
            
            names = [field.name for field in fields]
            self.assertEqual(names, sorted(names, reverse=True))  # Should be reverse sorted

    def test_combined_search_and_filter(self):
        """Test combining search, filter, and sort"""
        with self.app.app_context():
            # Search for fields in Cairo with price <= 100, sorted by price
            query = Field.query.filter(
                Field.governorate == 'Cairo',
                Field.price_per_hour <= 100
            ).order_by(Field.price_per_hour.asc())
            
            fields = query.all()
            
            # Should find 2 fields (Economy C: 75, Basic E: 50)
            self.assertEqual(len(fields), 2)
            
            # Should be sorted by price ascending
            prices = [field.price_per_hour for field in fields]
            self.assertEqual(prices, sorted(prices))
            
            # All should be in Cairo
            for field in fields:
                self.assertEqual(field.governorate, 'Cairo')
                
            # All should have price <= 100
            for field in fields:
                self.assertLessEqual(field.price_per_hour, 100)

if __name__ == '__main__':
    unittest.main()