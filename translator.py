"""Транслятор .aboba в машинный код."""

import sys

import isa
from isa import AddressMode, ArithmeticArgs, CmpArgs, InOutArgs, JumpArgs, MoveArgs, Opcode, Term


def clean_source(src):
    """Удаляет комментарии, пустые строки, секцию .data"""
    return "\n".join(line.split(";")[0].strip() for line in src.split("\n") if line.strip())


def remove_data(src):
    """Удаляет секцию .data"""
    return src[:src.index(".data")]


def get_register(args):
    """Преобразует аргументы вида "rN" в число N (для упрощения работы)."""
    for k in range(len(args)):
        if args[k].startswith("r"):
            args[k] = int(args[k][1:])
    return args


def parse_data(src):
    data = []
    lines = src.split("\n")
    lines = lines[lines.index(".data") + 1:lines.index(".code")]
    for i, line in enumerate(lines):
        words = line.split('"')
        data.append({"index": i, "label": words[0].strip(), "value": words[1], "length": int(words[2])})
    return data


def translate(source, labels):
    """Транслирует исходный код в машинный."""
    opcodes = []
    for i, line in enumerate(source.split("\n")):
        opcode = line.split(" ", 1)[0]
        if opcode.endswith(":") or opcode.startswith(".") or not opcode:
            continue
        opcode = Opcode(opcode)
        args = line.split(" ")[1:]
        args = get_register(args)
        assert opcode.terms_count == len(args), f"Invalid args for {opcode} at line {i}"
        if opcode in (Opcode.JMP, Opcode.JZ, Opcode.JNZ):
            if args[0] in labels:
                opcodes.append(
                    {
                        "index": len(opcodes),
                        "opcode": opcode,
                        "args": JumpArgs(AddressMode.ABS, labels[args[0]]),
                        "term": Term(i, args[0], str(opcode)),
                    }
                )
        elif opcode in (Opcode.ADD, Opcode.SUB, Opcode.MOD):
            opcodes.append(
                {
                    "index": len(opcodes),
                    "opcode": opcode,
                    "args": ArithmeticArgs(*args),
                    "term": Term(i, None, str(opcode)),
                }
            )
        elif opcode in (Opcode.IN, Opcode.OUT):
            opcodes.append(
                {
                    "index": len(opcodes),
                    "opcode": opcode,
                    "args": InOutArgs(args[0]),
                    "term": Term(i, None, str(opcode)),
                }
            )
        elif opcode in (Opcode.LOAD, Opcode.STORE, Opcode.MOVE):
            is_direct = args[1].startswith("#")
            if is_direct:
                args[1] = int(args[1][1:])
            opcodes.append(
                {"index": len(opcodes), "opcode": opcode, "args": MoveArgs(args[0], args[1], is_direct),
                 "term": Term(i, None, str(opcode))}
            )
        elif opcode in Opcode.CMP:
            opcodes.append(
                {"index": len(opcodes), "opcode": opcode, "args": CmpArgs(*args), "term": Term(i, None, str(opcode))}
            )
        elif opcode in Opcode.INC:
            opcodes.append(
                {"index": len(opcodes), "opcode": opcode, "args": (args[0]), "term": Term(i, None, str(opcode))}
            )
        else:
            opcodes.append({"index": len(opcodes), "opcode": opcode, "args": args, "term": Term(i, None, str(opcode))})
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


def main(source, target):
    with open(source) as f:
        source = f.read()
    cleaned_source = clean_source(source)
    labels = parse_labels(cleaned_source)
    source_without_data = remove_data(cleaned_source)
    data = parse_data(cleaned_source)
    print(data)
    code = translate(source_without_data, labels)
    isa.write_code(target, code)

    print("source LoC:", len(source.split("\n")), "code instr:", len(code))


if __name__ == "__main__":
    assert len(sys.argv) == 3, "Wrong arguments: translator.py <input_file> with .aboba ext <target_file>"
    _, source, target = sys.argv
    if not source.endswith(".aboba"):
        print("Source file must have .aboba extension")
        sys.exit(1)
    main(source, target)
