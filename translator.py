"""Транслятор .aboba в машинный код."""

import isa
import sys
from isa import *


def clean_source(src):
    """Удаляет комментарии и пустые строки."""
    return "\n".join(line.split(";")[0].strip() for line in src.split("\n") if line.strip())


def translate(source, labels):
    """Транслирует исходный код в машинный."""
    opcodes = []
    for i, line in enumerate(source.split("\n")):
        opcode = line.split(" ", 1)[0]
        if opcode.endswith(":"):
            continue
        opcode = Opcode(opcode)
        args = line.split(" ")[1:]
        assert opcode.terms_count == len(args), f"Invalid args for {opcode} at line {i}"
        if opcode in (Opcode.JMP, Opcode.JZ, Opcode.JNZ):
            if args[0] in labels:
                opcodes.append(
                    {"index": len(opcodes), "opcode": opcode, "args": JumpArgs(AddressMode.ABS, labels[args[0]]),
                     "term": Term(i, args[0], str(opcode))})
        elif opcode in (Opcode.ADD, Opcode.SUB, Opcode.MOD):
            opcodes.append({"index": len(opcodes), "opcode": opcode, "args": ArithmeticArgs(*args),
                            "term": Term(i, None, str(opcode))})
        elif opcode in (Opcode.IN, Opcode.OUT):
            opcodes.append({"index": len(opcodes), "opcode": opcode, "args": InOutArgs(args[0]),
                            "term": Term(i, None, str(opcode))})
        elif opcode in (Opcode.LOAD, Opcode.STORE, Opcode.MOVE):
            opcodes.append({"index": len(opcodes), "opcode": opcode, "args": MoveArgs(*args),
                            "term": Term(i, None, str(opcode))})
        elif opcode in Opcode.CMP:
            opcodes.append({"index": len(opcodes), "opcode": opcode, "args": CmpArgs(*args),
                            "term": Term(i, None, str(opcode))})
        elif opcode in Opcode.INC:
            opcodes.append({"index": len(opcodes), "opcode": opcode, "args": (args[0]),
                            "term": Term(i, None, str(opcode))})
        else:
            opcodes.append({"index": len(opcodes), "opcode": opcode, "args": args,
                            "term": Term(i, None, str(opcode))})
    return opcodes


def parse_labels(source):
    labels = {}
    for i, line in enumerate(source.split("\n")):
        line = line.split(";", 1)[0].strip()
        if not line:
            continue
        if line.endswith(":"):
            label = line[:-1]
            labels[label] = i
    return labels


# def parse_labels_and_opcodes(source):
#     labels = {}
#     opcodes = []
#     for i, line in enumerate(source.split("\n")):
#         line = line.split(";", 1)[0].strip()
#         if not line:
#             continue
#         tokens = line.split(" ")
#         if len(tokens) == 1:
#             if line.endswith(":"):
#                 label = line[:-1]
#                 labels[label] = len(opcodes)
#             else:
#                 opcode = Opcode(tokens[0])
#                 assert opcode.terms_count == len(tokens)-1, f"Invalid opcode {opcode} at line {i}"
#                 if opcode in (Opcode.JMP, Opcode.JZ, Opcode.JNZ):
#                     opcodes.append({"index": len(opcodes), "opcode": opcode, "term": Term(i, 0)})
#                 opcodes.append({"index": len(opcodes), "opcode": opcode, "term": Term(i, 0, tokens[0])})
#
#
#     return labels, opcodes


def main(source, target):
    with open(source, 'r') as f:
        source = f.read()
    cleaned_source = clean_source(source)
    labels = parse_labels(cleaned_source)
    code = translate(cleaned_source, labels)
    print(code)
    isa.write_code(target, code)

    print("source LoC:", len(source.split("\n")), "code instr:", len(code))


if __name__ == "__main__":
    assert len(sys.argv) == 3, "Wrong arguments: translator.py <input_file> with .aboba ext <target_file>"
    _, source, target = sys.argv
    if not source.endswith(".aboba"):
        print("Source file must have .aboba extension")
        sys.exit(1)
    main(source, target)
