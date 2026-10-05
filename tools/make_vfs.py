"""Создание тестовых ZIP-архивов VFS в папке build."""

import os
import zipfile

BUILD_DIR = "build"

MINIMAL = {
    "hello.txt": b"hello\n",
}

SEVERAL = {
    "a.txt": b"first file\n",
    "b.txt": b"second file\n",
    "c.txt": "строка 1\nстрока 2\nстрока 3\n".encode("utf-8"),
}

DEEP = {
    "readme.txt": b"deep vfs\n",
    "docs/guide.txt": b"level 1\n",
    "docs/manuals/intro.txt": b"level 2\n",
    "docs/manuals/deep/notes.txt": b"level 3\n",
    "docs/manuals/deep/data.bin": bytes(range(16)),
}

ARCHIVES = {
    "vfs_minimal.zip": MINIMAL,
    "vfs_several.zip": SEVERAL,
    "vfs_deep.zip": DEEP,
}


def write_archive(path, files):
    """Записать словарь {путь: байты} в ZIP-архив."""
    with zipfile.ZipFile(path, "w") as archive:
        for name, data in files.items():
            archive.writestr(name, data)


def main():
    """Создать все тестовые архивы."""
    os.makedirs(BUILD_DIR, exist_ok=True)
    for name, files in ARCHIVES.items():
        write_archive(os.path.join(BUILD_DIR, name), files)
        print(f"создан {name}")


if __name__ == "__main__":
    main()
