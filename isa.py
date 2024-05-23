import enum
import json
from collections import namedtuple


class Opcode(str, enum.Enum):
    """Опкоды инструкций."""

    LOAD = "load", 2  # Загрузка значения из памяти в регистр
    STORE = "store", 2  # Сохранение значения из регистра в память

    ADD = "add", 3  # Сложение
    SUB = "sub", 3  # Вычитание
    MOD = "mod", 3  # Остаток от деления
    INC = "inc", 3  # Увеличение на единицу

    CMP = "cmp", 2  # Сравнение

    IN = "in", 1  # Ввод данных из внешнего порта
    OUT = "out", 1  # Вывод данных во внешний порт

    JZ = "jz", 1  # Переход, если флаг нуля
    JNZ = "jnz", 1  # Переход, если нет флага нуля
    JMP = "jmp", 1  # Безусловный переход

    MOVE = "move", 2  # Перемещение данных между регистрами

    HALT = "halt", 0  # Остановка выполнения программы

    def __new__(cls, value, terms_count):
        obj = str.__new__(cls, value)
        obj._value_ = value
        obj.terms_count = terms_count
        return obj

    def __str__(self):
        return self.value


class AddressMode(str, enum.Enum):
    """Режимы адресации"""

    ABS = "absolute"
    REL = "relative"
    DATA = "data"
    REG = "register"

    def __str__(self):
        return self.value


class Term(namedtuple("Term", "line related_label opcode")):
    """
    Представляет отладочную информацию
    """


class JumpArgs(namedtuple("Args", "mode addr")):
    """
    Представляет аргументы инструкции
    """


class ArithmeticArgs(namedtuple("Args", "to operand1 operand2")):
    """
    Представляет аргументы арифметической инструкции
    """


class MoveArgs(namedtuple("Args", "from_ to")):
    """
    Представляет аргументы инструкции перемещения
    """


class InOutArgs(namedtuple("Args", "port")):
    """
    Представляет аргументы инструкции ввода/вывода
    """


class CmpArgs(namedtuple("Args", "operand1 operand2")):
    """
    Представляет аргументы инструкции сравнения
    """


def write_code(filename, code):
    """Записать машинный код в файл."""
    with open(filename, "w", encoding="utf-8") as file:
        file.write(json.dumps(code, indent=4))


def read_code(filename):
    """Прочесть машинный код из файла."""
    with open(filename, encoding="utf-8") as file:
        code = json.loads(file.read())

    for instr in code:
        if "opcode" in instr:
            instr["opcode"] = Opcode(instr["opcode"])

        # Конвертация списка term в класс Term
        if "term" in instr:
            assert len(instr["term"]) == 3
            instr["term"] = Term(instr["term"][0], instr["term"][1], instr["term"][2])
        if "args" in instr:
            instr["args"] = tuple(instr["args"])

    return code
