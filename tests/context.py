"""Подключение папки src к путям поиска модулей."""

import importlib
import os
import sys

SRC = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "src")
sys.path.insert(0, SRC)


def load(name):
    """Импортировать модуль из папки src по имени."""
    return importlib.import_module(name)
