"""Тесты разбора аргументов команды head."""

import unittest

import context  # noqa: F401
import main


class ParseHeadArgsTest(unittest.TestCase):
    """Проверки функции parse_head_args."""

    def test_default_count(self):
        """Без -n берётся число строк по умолчанию."""
        self.assertEqual(
            main.parse_head_args(["a.txt"]), (main.HEAD_LINES, "a.txt")
        )

    def test_with_option(self):
        """Число строк берётся из параметра -n."""
        self.assertEqual(
            main.parse_head_args(["-n", "3", "a.txt"]), (3, "a.txt")
        )

    def test_bad_number(self):
        """Нечисловое значение после -n считается ошибкой."""
        self.assertIsNone(main.parse_head_args(["-n", "x", "a.txt"]))

    def test_no_args(self):
        """Без аргументов разбор возвращает None."""
        self.assertIsNone(main.parse_head_args([]))


if __name__ == "__main__":
    unittest.main()
