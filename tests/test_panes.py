import unittest

from econsole.geometry import Rect
from econsole.panes.base import Pane
from econsole.panes.manager import PaneManager


def make_pane(title="p"):
    return Pane(0, "test", title)


class PaneManagerTest(unittest.TestCase):
    def setUp(self):
        self.m = PaneManager()
        self.root = make_pane("root")
        self.root.persistent = True
        self.m.add(self.root)

    def test_add_allocates_ids_and_focuses(self):
        p = self.m.add(make_pane("a"))
        self.assertGreater(p.id, 0)
        self.assertEqual(self.m.focused_id, p.id)

    def test_persistent_pane_cannot_be_removed(self):
        self.assertFalse(self.m.remove(self.root.id))
        self.assertIn(self.root, self.m.panes)

    def test_hide_and_show(self):
        p = self.m.add(make_pane("a"))
        self.assertTrue(self.m.hide(p.id))
        self.assertNotIn(p, self.m.visible_panes())
        self.assertIn(p, self.m.hidden_panes())
        self.m.show(p.id)
        self.assertIn(p, self.m.visible_panes())

    def test_hiding_focused_moves_focus(self):
        p = self.m.add(make_pane("a"))
        self.m.focus(p.id)
        self.m.hide(p.id)
        self.assertNotEqual(self.m.focused_id, p.id)

    def test_layout_tiles_visible_only(self):
        a = self.m.add(make_pane("a"))
        b = self.m.add(make_pane("b"))
        self.m.hide(b.id)
        layout = self.m.layout(Rect(0, 0, 80, 24))
        self.assertIn(self.root.id, layout)
        self.assertIn(a.id, layout)
        self.assertNotIn(b.id, layout)
        # Two visible panes split horizontally cover full width.
        self.assertEqual(layout[self.root.id].w + layout[a.id].w, 80)

    def test_zoom_shows_single_pane(self):
        a = self.m.add(make_pane("a"))
        self.m.focus(a.id)
        self.m.toggle_zoom()
        layout = self.m.layout(Rect(0, 0, 80, 24))
        self.assertEqual(list(layout.keys()), [a.id])
        self.assertEqual(layout[a.id], Rect(0, 0, 80, 24))

    def test_split_sets_orientation(self):
        self.m.set_orientation("h")
        p = make_pane("split")
        self.m.split(p, "down")
        self.assertEqual(self.m.orientation, "v")
        self.assertEqual(self.m.focused_id, p.id)

    def test_focus_next_cycles_visible(self):
        a = self.m.add(make_pane("a"))
        b = self.m.add(make_pane("b"))
        self.m.focus(self.root.id)
        self.m.focus_next()
        self.assertEqual(self.m.focused_id, a.id)
        self.m.focus_next()
        self.assertEqual(self.m.focused_id, b.id)
        self.m.focus_next()
        self.assertEqual(self.m.focused_id, self.root.id)

    def test_resize_changes_weight(self):
        a = self.m.add(make_pane("a"))
        self.m.focus(a.id)
        before = a.weight
        self.m.resize_focused(0.4)
        self.assertGreater(a.weight, before)

    def test_remove_refocuses(self):
        a = self.m.add(make_pane("a"))
        b = self.m.add(make_pane("b"))
        self.m.focus(b.id)
        self.m.remove(b.id)
        self.assertIn(self.m.focused_id, (self.root.id, a.id))


if __name__ == "__main__":
    unittest.main()
