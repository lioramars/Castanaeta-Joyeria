import unittest
from app import app, db

class AuthTests(unittest.TestCase):
    def setUp(self):
        app.config['TESTING'] = True
        app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'
        self.app = app.test_client()
        db.create_all()

    def tearDown(self):
        db.session.remove()
        db.drop_all()

    def test_register(self):
        response = self.app.post('/auth/register', data=dict(
            name='Test User',
            email='test@example.com',
            password='password',
            confirm_password='password'
        ))
        self.assertEqual(response.status_code, 302)

    def test_login(self):
        response = self.app.post('/auth/login', data=dict(
            email='test@example.com',
            password='password'
        ))
        self.assertEqual(response.status_code, 200)

    def test_reset_password(self):
        response = self.app.post('/auth/reset_password', data=dict(
            email='test@example.com'
        ))
        self.assertEqual(response.status_code, 200)

if __name__ == '__main__':
    unittest.main()
