import math
import unittest

from econsole.calc import CalcError, evaluate, format_result


class CalcTest(unittest.TestCase):
    def test_basic_arithmetic(self):
        self.assertEqual(evaluate("42*17"), 714)
        self.assertEqual(evaluate("2 + 3 * 4"), 14)
        self.assertEqual(evaluate("(2 + 3) * 4"), 20)
        self.assertEqual(evaluate("2 ** 10"), 1024)
        self.assertEqual(evaluate("7 // 2"), 3)
        self.assertEqual(evaluate("7 % 2"), 1)
        self.assertEqual(evaluate("-5 + 2"), -3)

    def test_functions_and_constants(self):
        self.assertAlmostEqual(evaluate("sqrt(16)"), 4.0)
        self.assertAlmostEqual(evaluate("sin(0)"), 0.0)
        self.assertAlmostEqual(evaluate("pi"), math.pi)
        self.assertEqual(evaluate("max(1, 9, 4)"), 9)

    def test_format_result(self):
        self.assertEqual(format_result(714.0), "714")
        self.assertEqual(format_result(3.5), "3.5")

    def test_rejects_unsafe_input(self):
        for expr in ("__import__('os')", "open('x')", "a.b", "1; 2", "lambda: 1",
                     "[1,2]", "x", "len('a')"):
            with self.assertRaises(CalcError):
                evaluate(expr)

    def test_empty(self):
        with self.assertRaises(CalcError):
            evaluate("   ")


if __name__ == "__main__":
    unittest.main()
