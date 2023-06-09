"""User model tests."""

# run these tests like:
#
#    python -m unittest test_user_model.py


import os
from unittest import TestCase

from models import db, User, Message, Follow
from flask_bcrypt import Bcrypt

# BEFORE we import our app, let's set an environmental variable
# to use a different database for tests (we need to do this
# before we import our app, since that will have already
# connected to the database

os.environ['DATABASE_URL'] = "postgresql:///warbler_test"

# Now we can import app

from app import app

# Create our tables (we do this here, so we only create the tables
# once for all tests --- in each test, we'll delete the data
# and create fresh new clean test data

db.drop_all()
db.create_all()

bcrypt = Bcrypt()

class UserModelTestCase(TestCase):
    def setUp(self):
        User.query.delete()

        u1 = User.signup("u1", "u1@email.com", "password", None)
        u2 = User.signup("u2", "u2@email.com", "password", None)

        db.session.commit()
        self.u1_id = u1.id
        self.u2_id = u2.id

        self.client = app.test_client()

    def tearDown(self):
        db.session.rollback()

    def test_user_model(self):
        u1 = User.query.get(self.u1_id)

        # User should have no messages & no followers
        self.assertEqual(len(u1.messages), 0)
        self.assertEqual(len(u1.followers), 0)

    def test_signup(self):
        u3 = User.signup("u3", "u3@email.com", "password", None)

        db.session.commit()
        self.u3_id = u3.id

        u3 = db.session.get(User,self.u3_id)
        self.assertTrue(bcrypt.check_password_hash(u3.password, "password"))

    def test_auth_ok(self):
        u1 = db.session.get(User, self.u1_id)
        self.assertEqual(User.authenticate("u1", "password"), u1)

    def test_auth_fail_no_user(self):
        self.assertFalse(User.authenticate("user-X", "password"))

    def test_auth_ok_wrong_pwd(self):
        u1 = db.session.get(User,self.u1_id)
        self.assertFalse(User.authenticate("u1", "wrong"))

    