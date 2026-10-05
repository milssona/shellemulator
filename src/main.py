"""Эмулятор оболочки ОС: окно, параметры запуска, команды и VFS."""

import argparse
import getpass
import platform
import shlex
import tkinter

import vfs

MAX_CD_ARGS = 1
NOT_SET = "не задан"


def make_title():
    """Вернуть заголовок окна по данным реальной ОС."""
    return f"Эмулятор - [{getpass.getuser()}@{platform.node()}]"


def parse_args(argv=None):
    """Разобрать параметры командной строки."""
    parser = argparse.ArgumentParser(description="Эмулятор оболочки ОС")
    parser.add_argument("--vfs", help="путь к физическому расположению VFS")
    parser.add_argument("--script", help="путь к стартовому скрипту")
    return parser.parse_args(argv)


class EmulatorWindow:
    """Окно эмулятора с полем вывода и строкой ввода."""

    def __init__(self, args):
        """Создать окно и расположить элементы."""
        self.args = args
        self.closed = False
        self.vfs_root = vfs.default_vfs()
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
        self.print_vfs_info()

    def execute(self, line):
        """Выполнить команду. Вернуть True при успехе, False при ошибке."""
        try:
            words = shlex.split(line)
        except ValueError:
            self.print_line("ошибка: незакрытая кавычка")
            return False
        if not words:
            return True
        name, args = words[0], words[1:]
        handlers = {
            "exit": self.cmd_exit,
            "ls": self.cmd_ls,
            "cd": self.cmd_cd,
            "vfs-init": self.cmd_vfs_init,
        }
        handler = handlers.get(name)
        if handler is None:
            self.print_line(f"ошибка: неизвестная команда: {name}")
            return False
        return handler(args)

    def cmd_ls(self, args):
        """Заглушка команды ls: вывести имя и аргументы."""
        self.print_line(f"ls {args}")
        return True

    def cmd_cd(self, args):
        """Заглушка команды cd: вывести имя и аргументы."""
        if len(args) > MAX_CD_ARGS:
            self.print_line("ошибка: cd: слишком много аргументов")
            return False
        self.print_line(f"cd {args}")
        return True

    def cmd_exit(self, args):
        """Закрыть окно эмулятора."""
        if args:
            self.print_line("ошибка: exit не принимает аргументов")
            return False
        self.closed = True
        self.root.destroy()
        return True

    def cmd_vfs_init(self, args):
        """Заменить текущую VFS на VFS по умолчанию."""
        if args:
            self.print_line("ошибка: vfs-init не принимает аргументов")
            return False
        try:
            removed = vfs.clear_physical(self.args.vfs)
        except OSError as error:
            self.print_line(f"ошибка: не удалось очистить VFS: {error}")
            return False
        self.vfs_root = vfs.default_vfs()
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
            self.print_line("> " + line)
            if not self.execute(line):
                self.print_line(f"ошибка в скрипте, строка {number}")
                return
            if self.closed:
                return

    def on_enter(self, event):
        """Обработать нажатие Enter в строке ввода."""
        line = self.entry.get()
        self.entry.delete(0, "end")
        self.print_line("> " + line)
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
