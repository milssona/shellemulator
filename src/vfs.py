"""Виртуальная файловая система, которая хранится только в памяти.

Двоичные данные в исходном коде и при выводе представлены в base64.
"""

import base64
import io
import os
import zipfile

ENCODING = "utf-8"
NULL_BYTE = b"\x00"

DEFAULT_TEXT_FILES = {
    "readme.txt": "VFS по умолчанию\n",
    "docs/guide.txt": "Первая строка\nВторая строка\nТретья строка\n",
}

DEFAULT_BINARY_FILES = {
    "bin/data.bin": "AAECA/8=",
}


class VfsError(Exception):
    """Ошибка работы с виртуальной файловой системой."""


class Node:
    """Узел дерева VFS: файл или каталог."""

    def __init__(self, is_dir, data=b""):
        """Создать узел. Для каталога поле data не используется."""
        self.is_dir = is_dir
        self.data = data
        self.children = {}


def add_entry(root, path, is_dir, data=b""):
    """Добавить в дерево файл или каталог по пути из архива."""
    parts = [part for part in path.split("/") if part]
    if not parts:
        return
    node = root
    for part in parts[:-1]:
        node = node.children.setdefault(part, Node(is_dir=True))
    last = parts[-1]
    if is_dir:
        node.children.setdefault(last, Node(is_dir=True))
    else:
        node.children[last] = Node(is_dir=False, data=data)


def load_zip(path):
    """Прочитать ZIP-архив целиком в память и построить дерево VFS."""
    try:
        with open(path, "rb") as file:
            raw = file.read()
        archive = zipfile.ZipFile(io.BytesIO(raw))
    except (OSError, zipfile.BadZipFile) as error:
        raise VfsError(f"не удалось открыть VFS: {path}") from error
    root = Node(is_dir=True)
    with archive:
        for info in archive.infolist():
            data = b"" if info.is_dir() else archive.read(info)
            add_entry(root, info.filename, info.is_dir(), data)
    return root


def default_vfs():
    """Построить VFS по умолчанию, заданную прямо в коде."""
    root = Node(is_dir=True)
    for path, text in DEFAULT_TEXT_FILES.items():
        add_entry(root, path, False, text.encode(ENCODING))
    for path, encoded in DEFAULT_BINARY_FILES.items():
        add_entry(root, path, False, base64.b64decode(encoded))
    return root


def clear_physical(path):
    """Удалить файл архива VFS. Вернуть True, если файл был удалён."""
    if path and os.path.isfile(path):
        os.remove(path)
        return True
    return False


def count_nodes(root):
    """Посчитать файлы и каталоги в дереве (сам корень не считается)."""
    files = 0
    dirs = 0
    for child in root.children.values():
        if child.is_dir:
            sub_files, sub_dirs = count_nodes(child)
            files += sub_files
            dirs += sub_dirs + 1
        else:
            files += 1
    return files, dirs


def is_binary(data):
    """Определить, содержит ли файл двоичные данные."""
    if NULL_BYTE in data:
        return True
    try:
        data.decode(ENCODING)
    except UnicodeDecodeError:
        return True
    return False


def file_text(node):
    """Вернуть содержимое файла: текст или base64 для двоичных данных."""
    if is_binary(node.data):
        return base64.b64encode(node.data).decode("ascii")
    return node.data.decode(ENCODING)
