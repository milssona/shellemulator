"""Эмулятор оболочки ОС: окно, параметры запуска, команды и VFS."""

import argparse
import getpass
import platform
import shlex
import time
import tkinter

import vfs

MAX_PATH_ARGS = 1
HEAD_LINES = 10
HEAD_SHORT_ARGS = 1
HEAD_LONG_ARGS = 3
NOT_SET = "не задан"
HELP_WIDTH = 24

COMMAND_HELP = (
    ("ls [путь]", "вывести содержимое каталога"),
    ("cd [путь]", "сменить текущий каталог"),
    ("cat файл...", "вывести содержимое файлов"),
    ("head [-n ЧИСЛО] файл", "вывести первые строки файла"),
    ("touch файл...", "создать пустой файл в памяти"),
    ("date", "вывести текущие дату и время"),
    ("vfs-init", "заменить VFS на VFS по умолчанию"),
    ("help", "показать список команд"),
    ("exit", "закрыть эмулятор"),
)


def make_title():
    """Вернуть заголовок окна по данным реальной ОС."""
    return f"Эмулятор - [{getpass.getuser()}@{platform.node()}]"


def parse_args(argv=None):
    """Разобрать параметры командной строки."""
    parser = argparse.ArgumentParser(description="Эмулятор оболочки ОС")
    parser.add_argument("--vfs", help="путь к физическому расположению VFS")
    parser.add_argument("--script", help="путь к стартовому скрипту")
    return parser.parse_args(argv)


def parse_head_args(args):
    """Разобрать аргументы head. Вернуть (число строк, путь) или None."""
    if len(args) == HEAD_SHORT_ARGS:
        return HEAD_LINES, args[0]
    if len(args) == HEAD_LONG_ARGS and args[0] == "-n" and args[1].isdigit():
        return int(args[1]), args[2]
    return None


class EmulatorWindow:
    """Окно эмулятора с полем вывода и строкой ввода."""

    def __init__(self, args):
        """Создать окно и расположить элементы."""
        self.args = args
        self.closed = False
        self.vfs_root = vfs.default_vfs()
        self.cwd = []
        self.root = tkinter.Tk()
        self.root.title(make_title())
        self.output = tkinter.Text(self.root, state="disabled")
        self.output.pack(fill="both", expand=True)
        self.entry = tkinter.Entry(self.root)
        self.entry.pack(fill="x")
        self.entry.bind("<Return>", self.on_enter)
        self.entry.focus_set()

    def print_line(self, text):
        """Добавить строку в поле вывода."""
        self.output.config(state="normal")
        self.output.insert("end", text + "\n")
        self.output.see("end")
        self.output.config(state="disabled")

    def print_debug(self):
        """Вывести в окно все заданные параметры запуска."""
        self.print_line("Параметры запуска:")
        self.print_line(f"  путь к VFS: {self.args.vfs or NOT_SET}")
        self.print_line(f"  стартовый скрипт: {self.args.script or NOT_SET}")

    def print_vfs_info(self):
        """Вывести краткие сведения о текущей VFS."""
        files, dirs = vfs.count_nodes(self.vfs_root)
        self.print_line(f"VFS: файлов {files}, каталогов {dirs}")

    def load_vfs(self):
        """Загрузить VFS из архива, а при ошибке взять VFS по умолчанию."""
        path = self.args.vfs
        if path:
            try:
                self.vfs_root = vfs.load_zip(path)
            except vfs.VfsError as error:
                self.print_line(f"ошибка: {error}")
                self.print_line("используется VFS по умолчанию")
        self.cwd = []
        self.print_vfs_info()

    def prompt(self):
        """Вернуть приглашение к вводу с текущим каталогом."""
        return "/" + "/".join(self.cwd) + "$ "

    def fail(self, message):
        """Вывести сообщение об ошибке и вернуть False."""
        self.print_line(f"ошибка: {message}")
        return False

    def execute(self, line):
        """Выполнить команду. Вернуть True при успехе, False при ошибке."""
        try:
            words = shlex.split(line)
        except ValueError:
            return self.fail("незакрытая кавычка")
        if not words:
            return True
        name, args = words[0], words[1:]
        handlers = {
            "exit": self.cmd_exit,
            "ls": self.cmd_ls,
            "cd": self.cmd_cd,
            "cat": self.cmd_cat,
            "head": self.cmd_head,
            "touch": self.cmd_touch,
            "date": self.cmd_date,
            "vfs-init": self.cmd_vfs_init,
            "help": self.cmd_help,
        }
        handler = handlers.get(name)
        if handler is None:
            return self.fail(f"неизвестная команда: {name}")
        return handler(args)

    def cmd_ls(self, args):
        """Вывести содержимое каталога: ls [путь]."""
        if len(args) > MAX_PATH_ARGS:
            return self.fail("ls: слишком много аргументов")
        path = args[0] if args else "."
        try:
            node, _ = vfs.resolve(self.vfs_root, self.cwd, path)
        except vfs.VfsError as error:
            return self.fail(f"ls: {error}")
        if node.is_dir:
            for name in sorted(node.children):
                self.print_line(name)
        else:
            self.print_line(path)
        return True

    def cmd_cd(self, args):
        """Сменить текущий каталог: cd [путь]."""
        if len(args) > MAX_PATH_ARGS:
            return self.fail("cd: слишком много аргументов")
        path = args[0] if args else "/"
        try:
            node, parts = vfs.resolve(self.vfs_root, self.cwd, path)
        except vfs.VfsError as error:
            return self.fail(f"cd: {error}")
        if not node.is_dir:
            return self.fail(f"cd: {path}: не является каталогом")
        self.cwd = parts
        return True

    def read_file(self, path, command):
        """Вернуть узел-файл по пути или None, если это ошибка."""
        try:
            node, _ = vfs.resolve(self.vfs_root, self.cwd, path)
        except vfs.VfsError as error:
            self.fail(f"{command}: {error}")
            return None
        if node.is_dir:
            self.fail(f"{command}: {path}: это каталог")
            return None
        return node

    def cmd_cat(self, args):
        """Вывести содержимое файлов: cat файл..."""
        if not args:
            return self.fail("cat: не указан файл")
        for path in args:
            node = self.read_file(path, "cat")
            if node is None:
                return False
            for line in vfs.file_lines(node):
                self.print_line(line)
        return True

    def cmd_head(self, args):
        """Вывести первые строки файла: head [-n ЧИСЛО] файл."""
        parsed = parse_head_args(args)
        if parsed is None:
            return self.fail("head: использование: head [-n ЧИСЛО] файл")
        count, path = parsed
        node = self.read_file(path, "head")
        if node is None:
            return False
        for line in vfs.file_lines(node)[:count]:
            self.print_line(line)
        return True

    def cmd_touch(self, args):
        """Создать пустые файлы в памяти: touch файл..."""
        if not args:
            return self.fail("touch: не указан файл")
        for path in args:
            try:
                vfs.create_file(self.vfs_root, self.cwd, path)
            except vfs.VfsError as error:
                return self.fail(f"touch: {error}")
        return True

    def cmd_help(self, args):
        """Вывести список команд с описанием."""
        if args:
            return self.fail("help: команда не принимает аргументов")
        for usage, description in COMMAND_HELP:
            self.print_line(f"{usage:<{HELP_WIDTH}}{description}")
        return True

    def cmd_date(self, args):
        """Вывести текущие дату и время."""
        if args:
            return self.fail("date: команда не принимает аргументов")
        self.print_line(time.asctime())
        return True

    def cmd_exit(self, args):
        """Закрыть окно эмулятора."""
        if args:
            return self.fail("exit: команда не принимает аргументов")
        self.closed = True
        self.root.destroy()
        return True

    def cmd_vfs_init(self, args):
        """Заменить текущую VFS на VFS по умолчанию."""
        if args:
            return self.fail("vfs-init: команда не принимает аргументов")
        try:
            removed = vfs.clear_physical(self.args.vfs)
        except OSError as error:
            return self.fail(f"vfs-init: не удалось очистить VFS: {error}")
        self.vfs_root = vfs.default_vfs()
        self.cwd = []
        if removed:
            self.print_line(f"файл VFS удалён: {self.args.vfs}")
        self.print_line("VFS заменена на VFS по умолчанию")
        self.print_vfs_info()
        return True

    def run_script(self, path):
        """Выполнить стартовый скрипт, остановившись на первой ошибке."""
        try:
            with open(path, encoding="utf-8") as file:
                lines = file.read().splitlines()
        except OSError:
            self.print_line(f"ошибка: не удалось открыть скрипт {path}")
            return
        for number, line in enumerate(lines, start=1):
            self.print_line(self.prompt() + line)
            if not self.execute(line):
                self.print_line(f"ошибка в скрипте, строка {number}")
                return
            if self.closed:
                return

    def on_enter(self, event):
        """Обработать нажатие Enter в строке ввода."""
        line = self.entry.get()
        self.entry.delete(0, "end")
        self.print_line(self.prompt() + line)
        self.execute(line)

    def run(self):
        """Показать параметры, загрузить VFS, запустить скрипт и окно."""
        self.print_debug()
        self.load_vfs()
        if self.args.script:
            self.root.after(0, self.run_script, self.args.script)
        self.root.mainloop()


def main():
    """Разобрать параметры, создать окно эмулятора и запустить его."""
    window = EmulatorWindow(parse_args())
    window.run()


if __name__ == "__main__":
    main()
