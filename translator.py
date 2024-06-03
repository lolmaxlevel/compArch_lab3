"""Транслятор .aboba в машинный код."""

import sys

import isa
from isa import AddressMode, ArithmeticArgs, CmpArgs, InOutArgs, JumpArgs, MoveArgs, Opcode, Term


def clean_source(src):
    """Удаляет комментарии, пустые строки, секцию .data"""
    return "\n".join(line.split(";")[0].strip() for line in src.split("\n") if line.strip())


def remove_data(src):
    """Удаляет секцию .data"""
    return src[src.index(".code") + 6 :]


def get_register(args):
    """Преобразует аргументы вида "rN" в число N (для упрощения работы)."""
    for k in range(len(args)):
        if args[k].startswith("r"):
            args[k] = int(args[k][1:])
    return args


def parse_data(src):
    """Получает данные из секции .data"""
    data = []
    lines = src.split("\n")
    lines = lines[lines.index(".data") + 1 : lines.index(".code")]
    for i, line in enumerate(lines):
        words = line.split('"')
        data.append({"index": i, "label": words[0].strip(), "value": words[1], "length": int(words[2])})
    return data


def handle_jump(opcode, args, labels, opcodes, i):
    if args[0] in labels:
        opcodes.append(
            {
                "index": len(opcodes),
                "opcode": opcode,
                "args": JumpArgs(AddressMode.ABS, labels[args[0]]),
                "term": Term(i, args[0], str(opcode)),
            }
        )


def handle_arithmetic(opcode, args, opcodes, i):
    opcodes.append(
        {
            "index": len(opcodes),
            "opcode": opcode,
            "args": ArithmeticArgs(*args),
            "term": Term(i, None, str(opcode)),
        }
    )


def handle_io(opcode, args, opcodes, i):
    opcodes.append(
        {
            "index": len(opcodes),
            "opcode": opcode,
            "args": InOutArgs(args[0]),
            "term": Term(i, None, str(opcode)),
        }
    )


def handle_move(opcode, args, opcodes, i):
    try:
        is_direct = args[1].startswith("#")
        if is_direct:
            args[1] = int(args[1][1:])
        opcodes.append(
            {
                "index": len(opcodes),
                "opcode": opcode,
                "args": MoveArgs(args[0], args[1], AddressMode.DIRECT),
                "term": Term(i, None, str(opcode)),
            }
        )
    except AttributeError:
        opcodes.append(
            {
                "index": len(opcodes),
                "opcode": opcode,
                "args": MoveArgs(args[0], args[1], AddressMode.REG),
                "term": Term(i, None, str(opcode)),
            }
        )


def handle_memory(opcode, args, opcodes, i):
    if not isinstance(args[1], int) and args[1].startswith("$"):
        opcodes.append(
            {
                "index": len(opcodes),
                "opcode": opcode,
                "args": MoveArgs(args[0], args[1], AddressMode.DATA),
                "term": Term(i, None, str(opcode)),
            }
        )
    else:
        opcodes.append(
            {
                "index": len(opcodes),
                "opcode": opcode,
                "args": MoveArgs(args[0], args[1], AddressMode.REG),
                "term": Term(i, None, str(opcode)),
            }
        )


def handle_cmp(opcode, args, opcodes, i):
    opcodes.append(
        {"index": len(opcodes), "opcode": opcode, "args": CmpArgs(*args), "term": Term(i, None, str(opcode))}
    )


def handle_inc(opcode, args, opcodes, i):
    opcodes.append({"index": len(opcodes), "opcode": opcode, "args": [args[0]], "term": Term(i, None, str(opcode))})


def translate(source, labels, data):
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
            handle_jump(opcode, args, labels, opcodes, i)
        elif opcode in (Opcode.ADD, Opcode.SUB, Opcode.MOD):
            handle_arithmetic(opcode, args, opcodes, i)
        elif opcode in (Opcode.IN, Opcode.OUT, Opcode.OUTN):
            handle_io(opcode, args, opcodes, i)
        elif opcode in (Opcode.MOVE):
            handle_move(opcode, args, opcodes, i)
        elif opcode in (Opcode.LOAD, Opcode.STORE):
            handle_memory(opcode, args, opcodes, i)
        elif opcode in Opcode.CMP:
            handle_cmp(opcode, args, opcodes, i)
        elif opcode in Opcode.INC:
            handle_inc(opcode, args, opcodes, i)
        else:
            opcodes.append({"index": len(opcodes), "opcode": opcode, "args": args, "term": Term(i, None, str(opcode))})
    add_data(opcodes, data)
    return opcodes


def add_data(opcodes, data):
    opcodes.extend(
        [
            {
                "index": len(opcodes) + sum(k["length"] for k in data[0:i]) + i,
                "opcode": "data",
                "args": [data[i]["value"], data[i]["length"]],
                "term": Term(i, data[i]["label"], "data"),
            }
            for i in range(len(data))
        ]
    )

    lengths = [k["length"] for k in data]
    data_labels = {data[i]["label"]: len(opcodes) - len(data) + sum(lengths[:i]) + i for i in range(len(data))}
    for opcode in opcodes:
        if opcode["opcode"] in (Opcode.LOAD, Opcode.STORE):
            if not isinstance(opcode["args"][1], int) and opcode["args"][1].startswith("$"):
                opcode["args"] = MoveArgs(data_labels[opcode["args"][1][1:]], opcode["args"][0], AddressMode.DATA)


def parse_labels(source):
    labels = {}
    counter = 0
    for i, line in enumerate(source.split("\n")):
        line = line.split(";", 1)[0].strip()
        if line.endswith(":"):
            i -= counter
            counter += 1
            label = line[:-1]
            labels[label] = i
    return labels


def main(source, target):
    with open(source) as f:
        source = f.read()
    cleaned_source = clean_source(source)
    source_without_data = remove_data(cleaned_source)
    labels = parse_labels(source_without_data)
    data = parse_data(cleaned_source)
    code = translate(source_without_data, labels, data)
    isa.write_code(target, code)

    print("source LoC:", len(source.split("\n")), "code instr:", len(code))


if __name__ == "__main__":
    assert len(sys.argv) == 3, "Wrong arguments: translator.py <input_file>.zxc <target_file>"
    _, source, target = sys.argv
    if not source.endswith(".zxc"):
        print("Source file must have .zxc extension")
        sys.exit(1)
    main(source, target)
