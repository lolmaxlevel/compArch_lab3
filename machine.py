import logging
import sys

from isa import AddressMode, Opcode, read_code


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
    def __init__(self, memory, memory_size, input_):
        assert memory_size > 0
        self.memory = [0] * memory_size
        self.registers = [0] * 8
        for i in range(len(memory)):
            self.memory[i] = memory[i]
        self.registers = Registers()
        self.input_ = input_
        self.output_buffer = []

    def read(self, address):
        return self.memory[address]

    def write(self, address, value):
        self.memory[address] = {"data": value}

    def signal_input(self, reg, port=0):
        try:
            self.registers.latch_register(reg, ord(self.input_.pop(0)))
        except IndexError:
            sys.exit(-12)

    def signal_output(self, reg, port=0):
        symbol = chr(self.registers.registers[reg])
        self.output_buffer.append(symbol)


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
        return 0

    def execute_memory(self, opcode, arg1, arg2, arg3):
        if opcode == Opcode.LOAD:
            if arg3 == AddressMode.DIRECT:
                self.data_path.registers.latch_register(arg1, arg2)
            elif arg3 == AddressMode.DATA:
                self.data_path.registers.latch_register(arg2, arg1)
            elif arg3 == AddressMode.REG:
                pos = self.data_path.registers.registers[arg2]
                self.data_path.registers.latch_register(arg1, self.data_path.read(pos)["args"])
        if opcode == Opcode.STORE:
            data = self.data_path.registers.registers[arg1]
            self.data_path.write(arg2, data)

    def execute_jump(self, opcode, arg1):
        if opcode == Opcode.JMP:
            self.instruction_counter = arg1
        if opcode == Opcode.JZ:
            if self.alu.zero_flag:
                self.instruction_counter = arg1
        if opcode == Opcode.JNZ:
            if not self.alu.zero_flag:
                self.instruction_counter = arg1

    def execute_in_out(self, opcode, arg1):
        if opcode == Opcode.IN:
            self.data_path.signal_input(arg1)
            self.tick()
        if opcode == Opcode.OUT:
            self.data_path.signal_output(arg1)
            self.tick()

    def execute_inc(self, opcode, arg1):
        if opcode == Opcode.INC:
            data = self.data_path.registers.registers[arg1]
            self.data_path.registers.latch_register(arg1, self.alu.inc(data))

    def execute_cmp(self, opcode, arg1, arg2):
        if opcode == Opcode.CMP:
            left = self.data_path.registers.registers[arg1]
            right = self.data_path.registers.registers[arg2]
            self.alu.cmp(left, right)

    def execute_move(self, opcode, arg1, arg2, arg3):
        if opcode == Opcode.MOVE:
            if arg3 == AddressMode.DIRECT:
                self.data_path.registers.latch_register(arg1, arg2)
            else:
                self.data_path.registers.latch_register(arg1, self.data_path.registers.registers[arg2])

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

        elif opcode in (Opcode.LOAD, Opcode.STORE):
            self.execute_memory(opcode, *args)
        elif opcode in (Opcode.IN, Opcode.OUT):
            self.execute_in_out(opcode, *args)
        elif opcode in (Opcode.CMP):
            self.execute_cmp(opcode, *args)
        elif opcode in (Opcode.INC):
            self.execute_inc(opcode, *args)
        elif opcode in (Opcode.JMP, Opcode.JZ, Opcode.JNZ):
            self.execute_jump(opcode, args[1] - 1)
        elif opcode in (Opcode.MOVE):
            self.execute_move(opcode, *args)
        elif opcode in (Opcode.HALT):
            raise StopIteration


def simulation(code, input_, data_memory_size, limit):
    data_path = DataPath(code, data_memory_size, input_)
    control_unit = ControlUnit(data_path)
    while control_unit.instruction_counter < len(code) and control_unit.ticks < limit:
        try:
            control_unit.decode_and_execute_instruction()
            print(control_unit.instruction_counter, control_unit.ticks, data_path.registers.registers)
        except StopIteration:
            break
        control_unit.instruction_counter += 1
    return data_path.output_buffer, control_unit.instruction_counter, control_unit.ticks


def main(code_file, input_file):
    code = read_code(code_file)
    # parsing data into separate instructions, probably should be moved to translator
    new_code = []
    for i in range(len(code)):
        if code[i]["opcode"] == Opcode.DATA:
            data_ = code[i]
            new_code.append({"index": data_["index"], "opcode": Opcode.DATA, "args": (data_["args"][1])})
            new_code.extend(
                [
                    {"index": data_["index"] + j + 1, "opcode": Opcode.DATA, "args": (ord(data_["args"][0][j]))}
                    for j in range(len(data_["args"][0]))
                ]
            )
        else:
            new_code.append(code[i])

    with open(input_file, encoding="utf-8") as file:
        input_text = file.read()
        input_token = []
        for char in input_text:
            input_token.append(char)
        output, instr_counter, ticks = simulation(
            new_code,
            input_token,
            100,
            10000,
        )
        print(output)
        print("".join(output))
        print("instr_counter: ", instr_counter, "ticks:", ticks)


if __name__ == "__main__":
    logging.getLogger().setLevel(logging.DEBUG)
    assert len(sys.argv) == 3, "Wrong arguments: machine.py <code_file> <input_file>"
    _, code_file, input_file = sys.argv
    main(code_file, input_file)
