import unittest

from econsole import easter
from econsole.theme import ROLES


def _valid_lines(lines):
    if not isinstance(lines, list) or not lines:
        return False
    valid_roles = set(ROLES) | {"text"}
    for item in lines:
        if not (isinstance(item, tuple) and len(item) == 2):
            return False
        text, role = item
        if not isinstance(text, str) or role not in valid_roles:
            return False
    return True


class EasterEggTest(unittest.TestCase):
    def test_train(self):
        self.assertTrue(_valid_lines(easter.train()))

    def test_cowsay_wraps_and_draws_cow(self):
        lines = easter.cowsay("hello there friend")
        self.assertTrue(_valid_lines(lines))
        text = "\n".join(t for t, _ in lines)
        self.assertIn("^__^", text)
        self.assertIn("hello", text)

    def test_cowsay_default(self):
        self.assertTrue(_valid_lines(easter.cowsay("")))

    def test_fortune(self):
        self.assertTrue(_valid_lines(easter.fortune()))

    def test_teapot(self):
        text = "\n".join(t for t, _ in easter.teapot())
        self.assertIn("418", text)

    def test_xyzzy(self):
        self.assertEqual(easter.xyzzy()[0][0], "Nothing happens.")

    def test_sudo_sandwich(self):
        self.assertEqual(easter.sudo(["make", "me", "a", "sandwich"]), [("Okay.", "ok")])

    def test_sudo_denied(self):
        lines = easter.sudo(["rm", "-rf", "/"])
        self.assertTrue(_valid_lines(lines))
        self.assertEqual(lines[0][1], "error")

    def test_matrix(self):
        text = "\n".join(t for t, _ in easter.matrix())
        self.assertIn("Neo", text)

    def test_calc_flavor(self):
        self.assertIn("Answer", easter.calc_flavor(42))
        self.assertIsNotNone(easter.calc_flavor(1337))
        self.assertIsNone(easter.calc_flavor(7))

    def test_eggs_catalogue(self):
        self.assertTrue(easter.EGGS)
        self.assertTrue(_valid_lines(easter.eggs_list()))


if __name__ == "__main__":
    unittest.main()
