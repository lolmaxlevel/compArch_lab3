import logging
import sys

from isa import Opcode, read_code


class Registers:
    # 8 registers for user, 2 for alu, 1 for io
    registers = None
    io = 0
    left_out: int = 0
    right_out: int = 0

    def __init__(self):
        self.registers = [0, 0, 0, 0, 0, 0, 0, 0]
        self.pc = 0
        self.io = 0
        self.left_out = 0
        self.right_out = 0

    def latch_register(self, register, value):
        self.registers[register] = value

    def latch_pc(self, value):
        self.registers.pc = value


class Alu:
    zero_flag = False

    def add(self, left, right):
        result = left + right
        self.zero_flag = result == 0
        return result

    def sub(self, left, right):
        result = left - right
        self.zero_flag = result == 0
        return result

    def cmp(self, left, right):
        result = left - right
        self.zero_flag = result == 0
        return result

    def inc(self, value):
        result = value + 1
        self.zero_flag = result == 0
        return result

    def mod(self, left, right):
        result = left % right
        self.zero_flag = result == 0
        return result

    def dec(self, value):
        result = value - 1
        self.zero_flag = result == 0
        return result


class DataPath:
    def __init__(self, memory, memory_size):
        assert memory_size > 0
        self.memory = [0] * memory_size
        self.registers = [0] * 8
        for i in range(len(memory)):
            self.memory[i] = memory[i]
        self.registers = Registers()

    def read(self, address):
        return self.memory[address]

    def write(self, address, value):
        self.memory[address] = {"data": value}

    def output(self, port):
        return self.registers.io


class ControlUnit:
    instruction_counter = 0
    ticks = 0

    def __init__(self, data_path):
        self.alu = Alu()
        self.data_path = data_path

    def tick(self):
        self.ticks += 1

    def execute_arithmetic(self, opcode, arg1, arg2):
        if opcode == Opcode.ADD:
            return self.alu.add(arg1, arg2)
        if opcode == Opcode.SUB:
            return self.alu.sub(arg1, arg2)
        if opcode == Opcode.MOD:
            return self.alu.mod(arg1, arg2)
        raise ValueError()

    def decode_and_execute_instruction(self):
        opcode = Opcode(self.data_path.read(self.instruction_counter)["opcode"])
        args = self.data_path.read(self.instruction_counter)["args"]
        self.tick()
        if opcode in (Opcode.ADD, Opcode.SUB, Opcode.MOD):
            self.data_path.registers.latch_register(
                args[0],
                self.execute_arithmetic(
                    opcode, self.data_path.registers.registers[args[1]], self.data_path.registers.registers[args[2]]
                ),
            )
            print("ADD/SUB/MOD", print(self.data_path.registers.registers))


def simulation(code, input_, data_memory_size, limit):
    data_path = DataPath(code, data_memory_size)
    control_unit = ControlUnit(data_path)
    while control_unit.instruction_counter < len(code) and control_unit.ticks < limit:
        control_unit.decode_and_execute_instruction()
    return [], 0, 0


def main(code_file, input_file):
    code = read_code(code_file)
    with open(input_file, encoding="utf-8") as file:
        input_text = file.read()
        input_token = []
        for char in input_text:
            input_token.append(char)

        output, instr_counter, ticks = simulation(
            code,
            input_token,
            100,
            1,
        )

        print("".join(output))
        print("instr_counter: ", instr_counter, "ticks:", ticks)


if __name__ == "__main__":
    logging.getLogger().setLevel(logging.DEBUG)
    assert len(sys.argv) == 3, "Wrong arguments: machine.py <code_file> <input_file>"
    _, code_file, input_file = sys.argv
    main(code_file, input_file)
