import unittest

from econsole.geometry import Rect


class GeometryTest(unittest.TestCase):
    def test_split_h_tiles_exactly(self):
        area = Rect(0, 0, 100, 30)
        rects = area.split_h([1, 1, 1])
        self.assertEqual(len(rects), 3)
        # No gaps, no overlaps, exact coverage.
        self.assertEqual(rects[0].x, 0)
        self.assertEqual(rects[-1].right, 100)
        for a, b in zip(rects, rects[1:]):
            self.assertEqual(a.right, b.x)
        self.assertEqual(sum(r.w for r in rects), 100)
        for r in rects:
            self.assertEqual(r.h, 30)

    def test_split_v_tiles_exactly(self):
        area = Rect(5, 2, 40, 21)
        rects = area.split_v([2, 1])
        self.assertEqual(rects[0].y, 2)
        self.assertEqual(rects[-1].bottom, 23)
        self.assertEqual(sum(r.h for r in rects), 21)
        # Weighted: first should be roughly twice the second.
        self.assertGreater(rects[0].h, rects[1].h)

    def test_weights_remainder_goes_to_last(self):
        area = Rect(0, 0, 10, 1)
        rects = area.split_h([1, 1, 1])  # 10 / 3 -> 3,3,4
        self.assertEqual([r.w for r in rects], [3, 3, 4])

    def test_inset_clamps_to_zero(self):
        r = Rect(0, 0, 4, 4).inset(3, 3, 3, 3)
        self.assertTrue(r.is_empty())

    def test_contains(self):
        r = Rect(2, 2, 3, 3)
        self.assertTrue(r.contains(2, 2))
        self.assertTrue(r.contains(4, 4))
        self.assertFalse(r.contains(5, 5))
        self.assertFalse(r.contains(1, 2))


if __name__ == "__main__":
    unittest.main()
