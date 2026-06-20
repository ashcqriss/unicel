import curses
import unittest

from econsole.widgets import InputField, truncate, wrap_text


class TruncateTest(unittest.TestCase):
    def test_truncate(self):
        self.assertEqual(truncate("hello", 10), "hello")
        self.assertEqual(truncate("hello world", 5), "hell…")
        self.assertEqual(truncate("abc", 0), "")


class WrapTest(unittest.TestCase):
    def test_wrap_preserves_blank_lines(self):
        wrapped = wrap_text("a\n\nb", 10)
        self.assertEqual(wrapped, ["a", "", "b"])

    def test_wrap_breaks_long_words(self):
        wrapped = wrap_text("abcdefghij", 4)
        self.assertTrue(all(len(line) <= 4 for line in wrapped))

    def test_wrap_words(self):
        wrapped = wrap_text("the quick brown fox", 9)
        self.assertTrue(all(len(line) <= 9 for line in wrapped))
        self.assertIn("the quick", wrapped)


class InputFieldTest(unittest.TestCase):
    def test_typing_and_submit(self):
        field = InputField()
        for ch in "hi":
            field.handle_key(ord(ch))
        self.assertEqual(field.text, "hi")
        action = field.handle_key(10)  # Enter
        self.assertEqual(action, ("submit", "hi"))

    def test_backspace_and_cursor(self):
        field = InputField("abc")
        field.handle_key(curses.KEY_LEFT)
        field.handle_key(curses.KEY_BACKSPACE)  # delete 'b'
        self.assertEqual(field.text, "ac")

    def test_cancel(self):
        field = InputField("x")
        self.assertEqual(field.handle_key(27), ("cancel", ""))

    def test_insert_in_middle(self):
        field = InputField("ac")
        field.handle_key(curses.KEY_LEFT)  # cursor between a and c
        field.handle_key(ord("b"))
        self.assertEqual(field.text, "abc")


if __name__ == "__main__":
    unittest.main()
