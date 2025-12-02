import unittest
from app import app, db, User

class BasicTests(unittest.TestCase):
    def setUp(self):
        app.config['TESTING'] = True
        app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'
        self.app = app.test_client()
        with app.app_context():
            db.create_all()

    def test_home(self):
        response = self.app.get('/')
        self.assertEqual(response.status_code, 200)

    def test_register(self):
        with app.app_context():
            response = self.app.post('/register', data=dict(username="test", password="123"), follow_redirects=True)
            self.assertEqual(response.status_code, 200)
            user = User.query.filter_by(username="test").first()
            self.assertIsNotNone(user)

if __name__ == "__main__":
    unittest.main()