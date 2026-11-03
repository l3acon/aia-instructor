"""Validation runs locally; DB tests run against CTFd's isolated TestingConfig."""
import copy
import importlib.util
from pathlib import Path
import unittest

spec = importlib.util.spec_from_file_location('ctfd_content', Path(__file__).parents[1] / 'files/ctfd_content.py')
runner = importlib.util.module_from_spec(spec)
spec.loader.exec_module(runner)
DEFINITION = dict(name='First', description='A test', category='Warm Up', value=10,
                  flags=[dict(content='synthetic-test-answer')], hints=[dict(content='A hint', cost=2)])


class Validation(unittest.TestCase):
    def test_invalid_definitions(self):
        for change in [dict(flags=[dict(content='CHANGEME')]), dict(prerequisites=['Missing']),
                       dict(type='dynamic'), dict(value=-1), dict(flags=[dict(content='[', type='regex')])]:
            with self.subTest(change=change), self.assertRaises(ValueError):
                runner.validate(dict(mode='update', challenges=[DEFINITION | change]))

    def test_duplicate_names(self):
        with self.assertRaises(ValueError):
            runner.validate(dict(mode='update', challenges=[DEFINITION, DEFINITION]))

    def test_cycles(self):
        with self.assertRaises(ValueError):
            runner.validate(dict(mode='update', challenges=[DEFINITION | dict(prerequisites=['Second']),
                            DEFINITION | dict(name='Second', prerequisites=['First'])]))

try:
    import CTFd
except ImportError:
    CTFd = None


@unittest.skipUnless(CTFd, 'Run DB tests inside the CTFd 3.7.7 container')
class Database(unittest.TestCase):
    def setUp(self):
        self.original = CTFd.create_app
        from CTFd.config import TestingConfig
        class IsolatedConfig(TestingConfig):
            SQLALCHEMY_ENGINE_OPTIONS = {}
            SQLALCHEMY_DATABASE_URI = 'sqlite://'
        self.app = self.original(IsolatedConfig)
        CTFd.create_app = lambda: self.app
        self.addCleanup(setattr, CTFd, 'create_app', self.original)
        from CTFd.models import db, Users
        self.context = self.app.app_context()
        self.context.push()
        self.addCleanup(self.context.pop)
        db.create_all()
        db.session.add(Users(name='unchanged-user', email='test@example.invalid', password='test-password'))
        db.session.commit()
        self.run_sync()

    def run_sync(self, mode='update', check=False, definitions=None):
        return runner.synchronize(dict(mode=mode, check=check, challenges=copy.deepcopy(definitions or [DEFINITION])))

    def state(self):
        from CTFd.models import Challenges, Hints, Flags, Users, Solves, Unlocks
        return dict(challenges=[(c.id,c.name,c.value) for c in Challenges.query.all()],
                    hints=[(h.id,h.content,h.cost) for h in Hints.query.all()],
                    flags=[(f.id,f.content) for f in Flags.query.all()],
                    users=[(u.id,u.name,u.password) for u in Users.query.all()],
                    solves=Solves.query.count(), unlocks=Unlocks.query.count())

    def add_progress(self):
        from CTFd.models import db, Users, Challenges, Hints, Solves, HintUnlocks, Awards, Fails
        uid, cid, hid = Users.query.first().id, Challenges.query.first().id, Hints.query.first().id
        db.session.add(Solves(user_id=uid, challenge_id=cid, provided='synthetic-test-answer'))
        db.session.add(Fails(user_id=uid, challenge_id=cid, provided='wrong-test-answer'))
        db.session.add(HintUnlocks(user_id=uid, target=hid))
        db.session.add(Awards(user_id=uid, name='Bonus', value=1))
        db.session.commit()

    def test_idempotence(self):
        before = self.state()
        self.assertFalse(self.run_sync()['changed'])
        self.assertEqual(before, self.state())

    def test_update_preserves_progress_and_ids(self):
        self.add_progress()
        before = self.state()
        self.run_sync(definitions=[DEFINITION | dict(value=15)])
        after = self.state()
        self.assertEqual(after['challenges'], [(before['challenges'][0][0], 'First', 15)])
        for field in ('hints','flags','users','solves','unlocks'):
            self.assertEqual(before[field], after[field])

    def test_check_rolls_back_reset_and_content(self):
        self.add_progress()
        before = self.state()
        self.assertTrue(self.run_sync(mode='reset', check=True, definitions=[DEFINITION | dict(value=50),
                            DEFINITION | dict(name='Second', prerequisites=['First'])])['changed'])
        self.assertEqual(before, self.state())

    def test_reset_keeps_accounts_and_clears_progress(self):
        self.add_progress()
        before = self.state()
        self.run_sync(mode='reset')
        after = self.state()
        self.assertEqual(before['users'], after['users'])
        self.assertEqual(after['solves'], 0)
        self.assertEqual(after['unlocks'], 0)
        from CTFd.models import Awards, Fails
        self.assertEqual(Awards.query.count(), 0)
        self.assertEqual(Fails.query.count(), 0)

    def test_inserted_hint_preserves_purchased_hint_id(self):
        self.add_progress()
        before = self.state()
        self.run_sync(definitions=[DEFINITION | dict(hints=[dict(content='New first hint', cost=1), *DEFINITION['hints']])])
        after = self.state()
        self.assertIn(before['hints'][0], after['hints'])
        self.assertEqual(after['unlocks'], before['unlocks'])

    def test_absent_challenges_are_retained(self):
        self.run_sync(definitions=[DEFINITION | dict(name='Second')])
        self.assertEqual(len(self.state()['challenges']), 2)

    def test_invalid_input_preserves_state(self):
        before = self.state()
        with self.assertRaises(ValueError):
            self.run_sync(mode='reset', definitions=[DEFINITION | dict(prerequisites=['missing'])])
        self.assertEqual(before, self.state())


if __name__ == '__main__':
    unittest.main()
