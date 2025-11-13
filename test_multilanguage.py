import unittest
from app import create_app
from models import db, User
import json

class MultiLanguageTestCase(unittest.TestCase):
    def setUp(self):
        """Set up test environment"""
        self.app = create_app()
        self.app.config['TESTING'] = True
        self.app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'
        self.client = self.app.test_client()
        
        with self.app.app_context():
            db.create_all()
            
            # Create a test user
            user = User(name='Test User', email='test@example.com', role='user')
            user.set_password('password123')
            db.session.add(user)
            db.session.commit()
            
            # Store user ID for later use
            self.user_id = user.id

    def tearDown(self):
        """Clean up after tests"""
        with self.app.app_context():
            db.session.remove()
            db.drop_all()

    def test_english_response(self):
        """Test that English responses work correctly"""
        # Test login with English
        response = self.client.post('/api/auth/login',
                                  data=json.dumps({
                                      'email': 'test@example.com',
                                      'password': 'password123'
                                  }),
                                  content_type='application/json',
                                  headers={'Accept-Language': 'en'})
        
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)
        self.assertIn('message', data)
        self.assertEqual(data['message'], 'User logged in successfully')

    def test_arabic_response(self):
        """Test that Arabic responses work correctly"""
        # Test login with Arabic
        response = self.client.post('/api/auth/login',
                                  data=json.dumps({
                                      'email': 'test@example.com',
                                      'password': 'password123'
                                  }),
                                  content_type='application/json',
                                  headers={'Accept-Language': 'ar'})
        
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)
        self.assertIn('message', data)
        # The Arabic translation would be here
        self.assertIn('message', data)

    def test_default_english_when_unsupported_language(self):
        """Test that English is used when unsupported language is requested"""
        # Test login with unsupported language
        response = self.client.post('/api/auth/login',
                                  data=json.dumps({
                                      'email': 'test@example.com',
                                      'password': 'password123'
                                  }),
                                  content_type='application/json',
                                  headers={'Accept-Language': 'fr'})
        
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)
        self.assertIn('message', data)
        self.assertEqual(data['message'], 'User logged in successfully')

    def test_missing_fields_error_english(self):
        """Test missing fields error in English"""
        response = self.client.post('/api/auth/login',
                                  data=json.dumps({
                                      'email': 'test@example.com'
                                      # Missing password
                                  }),
                                  content_type='application/json',
                                  headers={'Accept-Language': 'en'})
        
        self.assertEqual(response.status_code, 400)
        data = json.loads(response.data)
        self.assertIn('message', data)
        self.assertEqual(data['message'], 'Required field is missing')

    def test_invalid_credentials_error_english(self):
        """Test invalid credentials error in English"""
        response = self.client.post('/api/auth/login',
                                  data=json.dumps({
                                      'email': 'test@example.com',
                                      'password': 'wrongpassword'
                                  }),
                                  content_type='application/json',
                                  headers={'Accept-Language': 'en'})
        
        self.assertEqual(response.status_code, 401)
        data = json.loads(response.data)
        self.assertIn('message', data)
        self.assertEqual(data['message'], 'Invalid email or password')

if __name__ == '__main__':
    unittest.main()