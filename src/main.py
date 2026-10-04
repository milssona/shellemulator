"""Эмулятор оболочки ОС: прототип с графическим интерфейсом."""

import getpass
import platform
import shlex
import tkinter

MAX_CD_ARGS = 1


def make_title():
    """Вернуть заголовок окна по данным реальной ОС."""
    return f"Эмулятор - [{getpass.getuser()}@{platform.node()}]"


class EmulatorWindow:
    """Окно эмулятора с полем вывода и строкой ввода."""

    def __init__(self):
        """Создать окно и расположить элементы."""
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

    def execute(self, line):
        """Разобрать строку и выполнить команду."""
        try:
            words = shlex.split(line)
        except ValueError:
            self.print_line("ошибка: незакрытая кавычка")
            return
        if not words:
            return
        name, args = words[0], words[1:]
        if name == "exit":
            self.cmd_exit(args)
        elif name == "ls":
            self.print_line(f"ls {args}")
        elif name == "cd":
            self.cmd_cd(args)
        else:
            self.print_line(f"ошибка: неизвестная команда: {name}")

    def cmd_cd(self, args):
        """Заглушка команды cd: вывести имя и аргументы."""
        if len(args) > MAX_CD_ARGS:
            self.print_line("cd: слишком много аргументов")
        else:
            self.print_line(f"cd {args}")

    def cmd_exit(self, args):
        """Закрыть окно эмулятора."""
        if args:
            self.print_line("exit: команда не принимает аргументов")
        else:
            self.root.destroy()

    def on_enter(self, event):
        """Обработать нажатие Enter в строке ввода."""
        line = self.entry.get()
        self.entry.delete(0, "end")
        self.print_line("> " + line)
        self.execute(line)

    def run(self):
        """Запустить главный цикл окна."""
        self.root.mainloop()


def main():
    """Создать окно эмулятора и запустить его."""
    window = EmulatorWindow()
    window.run()


if __name__ == "__main__":
    main()