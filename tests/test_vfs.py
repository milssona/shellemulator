"""Тесты виртуальной файловой системы."""

import base64
import os
import tempfile
import unittest
import zipfile

import context

vfs = context.load("vfs")

BINARY = bytes(range(8))
FILES = {
    "readme.txt": b"hello\nworld\n",
    "docs/guide.txt": b"guide\n",
    "docs/deep/data.bin": BINARY,
}
FILE_COUNT = 3
DIR_COUNT = 2


def make_root():
    """Построить VFS из временного ZIP-архива."""
    with tempfile.TemporaryDirectory() as folder:
        path = os.path.join(folder, "test.zip")
        with zipfile.ZipFile(path, "w") as archive:
            for name, data in FILES.items():
                archive.writestr(name, data)
        return vfs.load_zip(path)


class VfsTest(unittest.TestCase):
    """Проверки загрузки и поиска узлов в VFS."""

    def test_count_nodes(self):
        """Файлы и каталоги подсчитываются правильно."""
        root = make_root()
        self.assertEqual(vfs.count_nodes(root), (FILE_COUNT, DIR_COUNT))

    def test_resolve_absolute(self):
        """Абсолютный путь ищется от корня."""
        root = make_root()
        node, parts = vfs.resolve(root, ["docs"], "/readme.txt")
        self.assertFalse(node.is_dir)
        self.assertEqual(parts, ["readme.txt"])

    def test_resolve_relative(self):
        """Относительный путь ищется от текущего каталога."""
        root = make_root()
        node, parts = vfs.resolve(root, ["docs"], "deep")
        self.assertTrue(node.is_dir)
        self.assertEqual(parts, ["docs", "deep"])

    def test_resolve_parent(self):
        """Часть .. поднимает на уровень вверх, в корне остаётся корень."""
        root = make_root()
        _, parts = vfs.resolve(root, ["docs", "deep"], "../..")
        self.assertEqual(parts, [])
        _, parts = vfs.resolve(root, [], "..")
        self.assertEqual(parts, [])

    def test_resolve_missing(self):
        """Несуществующий путь вызывает ошибку VFS."""
        root = make_root()
        with self.assertRaises(vfs.VfsError):
            vfs.resolve(root, [], "nope.txt")

    def test_file_lines_text(self):
        """Текстовый файл читается построчно."""
        root = make_root()
        node, _ = vfs.resolve(root, [], "readme.txt")
        self.assertEqual(vfs.file_lines(node), ["hello", "world"])

    def test_file_lines_binary(self):
        """Двоичный файл выводится в формате base64."""
        root = make_root()
        node, _ = vfs.resolve(root, [], "docs/deep/data.bin")
        expected = base64.b64encode(BINARY).decode("ascii")
        self.assertEqual(vfs.file_lines(node), [expected])

    def test_load_missing_archive(self):
        """Отсутствующий архив вызывает ошибку VFS."""
        with self.assertRaises(vfs.VfsError):
            vfs.load_zip("no_such_archive.zip")


class DefaultAndClearTest(unittest.TestCase):
    """Проверки VFS по умолчанию и удаления архива."""

    def test_default_has_readme(self):
        """В VFS по умолчанию есть файл readme.txt."""
        self.assertIn("readme.txt", vfs.default_vfs().children)

    def test_clear_physical(self):
        """Файл архива удаляется, повторное удаление ничего не делает."""
        with tempfile.TemporaryDirectory() as folder:
            path = os.path.join(folder, "old.zip")
            with open(path, "wb") as file:
                file.write(b"x")
            self.assertTrue(vfs.clear_physical(path))
            self.assertFalse(os.path.exists(path))
            self.assertFalse(vfs.clear_physical(path))


if __name__ == "__main__":
    unittest.main()
