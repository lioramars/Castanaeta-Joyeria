import unittest
from app import app, db

class DashboardTests(unittest.TestCase):
    def setUp(self):
        app.config['TESTING'] = True
        app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'
        self.app = app.test_client()
        db.create_all()

    def tearDown(self):
        db.session.remove()
        db.drop_all()

    def test_dashboard_access(self):
        response = self.app.get('/admin/dashboard')
        self.assertEqual(response.status_code, 200)

if __name__ == '__main__':
    unittest.main()
