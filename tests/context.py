"""Добавляет папку src в пути поиска модулей для тестов."""

import os
import sys

SRC_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "src")
sys.path.insert(0, os.path.normpath(SRC_DIR))
