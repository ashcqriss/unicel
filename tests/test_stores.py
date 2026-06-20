import datetime as dt
import unittest

from econsole.stores import ActivityStore, NotesStore, UserStore

from ._tmpenv import TempEnvTestCase


class ActivityStoreTest(TempEnvTestCase):
    def test_add_and_cycle_status(self):
        store = ActivityStore()
        item = store.add("task", "Write tests")
        self.assertEqual(item["status"], "open")
        store.cycle_status(item["id"])
        self.assertEqual(store.get(item["id"])["status"], "active")
        store.cycle_status(item["id"])
        self.assertEqual(store.get(item["id"])["status"], "done")
        self.assertIn("completed", store.get(item["id"]))
        store.cycle_status(item["id"])
        self.assertEqual(store.get(item["id"])["status"], "open")

    def test_persistence_roundtrip(self):
        store = ActivityStore()
        store.add("goal", "Ship E-Console")
        reloaded = ActivityStore()
        self.assertEqual(len(reloaded.all()), 1)
        self.assertEqual(reloaded.all()[0]["type"], "goal")

    def test_for_date_and_upcoming(self):
        store = ActivityStore()
        today = dt.date.today().isoformat()
        future = (dt.date.today() + dt.timedelta(days=3)).isoformat()
        store.add("event", "Standup", due=today)
        store.add("reminder", "Renew", due=future)
        self.assertEqual(len(store.for_date(today)), 1)
        self.assertEqual(len(store.upcoming()), 2)

    def test_unknown_type_becomes_task(self):
        store = ActivityStore()
        item = store.add("bogus", "x")
        self.assertEqual(item["type"], "task")

    def test_counts_by_type(self):
        store = ActivityStore()
        store.add("task", "a")
        store.add("task", "b")
        store.add("habit", "c")
        counts = store.counts_by_type()
        self.assertEqual(counts["task"], 2)
        self.assertEqual(counts["habit"], 1)


class NotesStoreTest(TempEnvTestCase):
    def test_add_update_remove(self):
        store = NotesStore()
        note = store.add("Title", "Body")
        self.assertEqual(note["title"], "Title")
        store.update(note["id"], body="New body")
        self.assertEqual(store.get(note["id"])["body"], "New body")
        self.assertTrue(store.remove(note["id"]))
        self.assertEqual(store.all(), [])


class UserStoreTest(TempEnvTestCase):
    def test_max_three_users(self):
        store = UserStore()
        store.add("Ada")
        store.add("Linus")
        store.add("Grace")
        with self.assertRaises(ValueError):
            store.add("Fourth")

    def test_duplicate_name_rejected(self):
        store = UserStore()
        store.add("Ada")
        with self.assertRaises(ValueError):
            store.add("ada")

    def test_empty_name_rejected(self):
        store = UserStore()
        with self.assertRaises(ValueError):
            store.add("   ")

    def test_default_avatar(self):
        store = UserStore()
        user = store.add("Ada")
        self.assertEqual(user["avatar"], "A")


if __name__ == "__main__":
    unittest.main()
