"""Тесты создания файлов в памяти (команда touch)."""

import unittest

import context  # noqa: F401
import vfs


class CreateFileTest(unittest.TestCase):
    """Проверки функции create_file."""

    def setUp(self):
        """Подготовить VFS по умолчанию перед каждым тестом."""
        self.root = vfs.default_vfs()

    def test_create_in_root(self):
        """Новый файл появляется в корне и пустой."""
        vfs.create_file(self.root, [], "new.txt")
        node, _ = vfs.resolve(self.root, [], "new.txt")
        self.assertFalse(node.is_dir)
        self.assertEqual(node.data, b"")

    def test_create_with_parent_path(self):
        """Путь с .. создаёт файл в родительском каталоге."""
        vfs.create_file(self.root, ["docs"], "../up.txt")
        self.assertIn("up.txt", self.root.children)

    def test_existing_file_not_changed(self):
        """Повторный touch не меняет содержимое файла."""
        before, _ = vfs.resolve(self.root, [], "readme.txt")
        data = before.data
        vfs.create_file(self.root, [], "readme.txt")
        after, _ = vfs.resolve(self.root, [], "readme.txt")
        self.assertEqual(after.data, data)

    def test_missing_parent(self):
        """Если родительского каталога нет, будет ошибка VFS."""
        with self.assertRaises(vfs.VfsError):
            vfs.create_file(self.root, [], "nope/file.txt")

    def test_parent_is_file(self):
        """Если родитель это файл, будет ошибка VFS."""
        with self.assertRaises(vfs.VfsError):
            vfs.create_file(self.root, [], "readme.txt/file.txt")

    def test_normalize(self):
        """Путь превращается в список имён от корня."""
        self.assertEqual(vfs.normalize(["docs"], "../x"), ["x"])
        self.assertEqual(vfs.normalize(["docs"], "/a/./b"), ["a", "b"])


if __name__ == "__main__":
    unittest.main()
