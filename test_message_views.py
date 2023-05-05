"""Message View tests."""

# run these tests like:
#
#    FLASK_DEBUG=False python3 -m unittest test_message_views.py


import os
from unittest import TestCase

from models import db, Message, User

# BEFORE we import our app, let's set an environmental variable
# to use a different database for tests (we need to do this
# before we import our app, since that will have already
# connected to the database

os.environ['DATABASE_URL'] = "postgresql:///warbler_test"

# Now we can import app

from app import app, CURR_USER_KEY

app.config['DEBUG_TB_INTERCEPT_REDIRECTS'] = False

# This is a bit of hack, but don't use Flask DebugToolbar

app.config['DEBUG_TB_HOSTS'] = ['dont-show-debug-toolbar']

# Create our tables (we do this here, so we only create the tables
# once for all tests --- in each test, we'll delete the data
# and create fresh new clean test data

db.drop_all()
db.create_all()

# Don't have WTForms use CSRF at all, since it's a pain to test

app.config['WTF_CSRF_ENABLED'] = False


class MessageBaseViewTestCase(TestCase):
    def setUp(self):
        User.query.delete()

        u1 = User.signup("u1", "u1@email.com", "password", None)
        db.session.flush()

        m1 = Message(text="m1-text", user_id=u1.id)
        db.session.add_all([m1])
        db.session.commit()

        self.u1_id = u1.id
        self.m1_id = m1.id

        self.client = app.test_client()

    def tearDown(self):
        """Clean up fouled transactions."""

        db.session.rollback()

class MessageAddViewTestCase(MessageBaseViewTestCase):
    def test_add_message(self):
        # Since we need to change the session to mimic logging in,
        # we need to use the changing-session trick:
        with self.client as c:
            with c.session_transaction() as sess:
                sess[CURR_USER_KEY] = self.u1_id

            # Now, that session setting is saved, so we can have
            # the rest of ours test
            resp = c.post("/messages/new", data={"text": "Hello"})

            self.assertEqual(resp.status_code, 302)
            self.assertEqual(resp.location, f"/users/{self.u1_id}")

            m = Message.query.filter_by(text="Hello").one()
            u = User.query.get(self.u1_id)

            self.assertIn(m, u.messages)
            self.assertEqual(len(u.messages), 2)
            self.assertEqual(m.user_id, self.u1_id)

    def test_show_message(self):
        with self.client as c:
            with c.session_transaction() as sess:
                sess[CURR_USER_KEY] = self.u1_id

            resp = c.get(f"/messages/{self.m1_id}")
            html = resp.get_data(as_text=True)

            self.assertEqual(resp.status_code, 200)
            self.assertIn("m1-text", html)
            self.assertIn("test messages route", html)

    def test_like_message(self):
        with self.client as c:
            with c.session_transaction() as sess:
                sess[CURR_USER_KEY] = self.u1_id

        u = User.query.get(self.u1_id)
        m = Message.query.get(self.m1_id)

        resp = c.post(f"/messages/{self.m1_id}/like")

        self.assertEqual(resp.status_code, 302)
        self.assertEqual(resp.location, f"/users/{self.u1_id}/likes")
        self.assertEqual(u.likes, [m])
        self.assertEqual(m.liked_by, [u])

class MessageDeleteViewTestCase(MessageBaseViewTestCase):
    def test_delete_message(self):
        with self.client as c:
            with c.session_transaction() as sess:
                sess[CURR_USER_KEY] = self.u1_id

            resp = c.post(f"/messages/{self.m1_id}/delete")
            u = User.query.get(self.u1_id)

            self.assertEqual(resp.status_code, 302)
            self.assertEqual(resp.location, f"/users/{self.u1_id}")
            self.assertEqual(u.messages, [])

    def test_unlike_message(self):
        with self.client as c:
            with c.session_transaction() as sess:
                sess[CURR_USER_KEY] = self.u1_id

        u = User.query.get(self.u1_id)
        m = Message.query.get(self.m1_id)

        u.likes.append(m)
        db.session.commit()

        resp = c.post(f"/messages/{self.m1_id}/unlike")

        self.assertEqual(resp.status_code, 302)
        self.assertEqual(resp.location, f"/users/{self.u1_id}/likes")
        self.assertEqual(u.likes, [])
        self.assertEqual(m.liked_by, [])