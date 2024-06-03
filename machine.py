import logging
import sys

from isa import AddressMode, Opcode, read_code


class Registers:
    # 8 registers for user, 2 for alu, 1 for io
    registers = None
    io = 0

    def __init__(self):
        self.registers = [0, 0, 0, 0, 0, 0, 0, 0, 0]
        self.io = 0

    def latch_register(self, register, value):
        self.registers[register] = value

    def latch_pc(self, value):
        self.registers.pc = value

    def get_register(self, register):
        return self.registers[register]


class Alu:
    zero_flag = False
    right = 0
    left = 0

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


class PortManager:
    def __init__(self, ports, registers):
        self.ports = ports
        self.registers = registers
        self.output_buffer = []

    def signal_input(self, reg, port=0):
        try:
            self.registers.latch_register(reg, ord(self.ports[port].pop(0)))
            logging.debug(f"input: '{chr(self.registers.get_register(reg))}'")
        except IndexError:
            logging.error("input buffer is empty")
            sys.exit(-12)

    def signal_output(self, reg, is_direct=False, port=0):
        if is_direct:
            symbol = str(self.registers.get_register(reg))
        else:
            symbol = chr(self.registers.get_register(reg))
        logging.debug(f"output: '{''.join(self.output_buffer)}' << '{symbol}'")
        self.output_buffer.append(symbol)


class DataPath:
    def __init__(self, memory, memory_size, input_):
        assert memory_size > 0
        self.memory = [0] * memory_size
        for i in range(len(memory)):
            self.memory[i] = memory[i]
        self.registers = Registers()
        self.output_buffer = []
        self.alu = Alu()
        self.port_manager = PortManager([input_], self.registers)

    def read(self, address):
        return self.memory[address]

    def write(self, address, value):
        self.memory[address] = {"data": value}


class ControlUnit:
    instruction_counter = 0
    ticks = 0

    def __init__(self, data_path):
        self.data_path = data_path
        self.opcode = None
        self.args = None

    def tick(self):
        self.ticks += 1

    def latch_pc(self, value):
        self.instruction_counter = value

    def execute_arithmetic(self, opcode, arg1, arg2):
        self.tick()
        if opcode == Opcode.ADD:
            return self.data_path.alu.add(arg1, arg2)
        if opcode == Opcode.SUB:
            return self.data_path.alu.sub(arg1, arg2)
        if opcode == Opcode.MOD:
            return self.data_path.alu.mod(arg1, arg2)
        self.tick()
        return 0

    def execute_memory(self, opcode, arg1, arg2, arg3):
        if opcode == Opcode.LOAD:
            if arg3 == AddressMode.DIRECT:
                self.data_path.registers.latch_register(arg1, arg2)
            elif arg3 == AddressMode.DATA:
                self.tick()
                self.data_path.registers.latch_register(arg2, arg1)
            elif arg3 == AddressMode.REG:
                pos = self.data_path.registers.get_register(arg2)
                self.tick()
                self.data_path.registers.latch_register(arg1, self.data_path.read(pos)["args"])
        if opcode == Opcode.STORE:
            data = self.data_path.registers.get_register(arg1)
            self.tick()
            self.data_path.write(arg2, data)
        self.tick()

    def execute_jump(self, opcode, arg1):
        if opcode == Opcode.JMP:
            self.latch_pc(arg1)
        if opcode == Opcode.JZ:
            if self.data_path.alu.zero_flag:
                self.latch_pc(arg1)
        if opcode == Opcode.JNZ:
            if not self.data_path.alu.zero_flag:
                self.latch_pc(arg1)
        self.tick()

    def execute_in_out(self, opcode, arg1):
        if opcode == Opcode.IN:
            self.data_path.port_manager.signal_input(arg1)
        if opcode == Opcode.OUT:
            self.data_path.port_manager.signal_output(arg1)
        if opcode == Opcode.OUTN:
            self.data_path.port_manager.signal_output(arg1, True)
        self.tick()

    def execute_inc(self, opcode, arg1):
        if opcode == Opcode.INC:
            self.tick()
            data = self.data_path.registers.get_register(arg1)
            self.data_path.registers.latch_register(arg1, self.data_path.alu.inc(data))
            self.tick()

    def execute_cmp(self, opcode, arg1, arg2):
        if opcode == Opcode.CMP:
            self.tick()
            left = self.data_path.registers.get_register(arg1)
            right = self.data_path.registers.get_register(arg2)
            self.data_path.alu.cmp(left, right)
            self.tick()

    def execute_move(self, opcode, arg1, arg2, arg3):
        if opcode == Opcode.MOVE:
            if arg3 == AddressMode.DIRECT:
                self.data_path.registers.latch_register(arg1, arg2)
            else:
                data = self.data_path.registers.get_register(arg2)
                self.tick()
                self.data_path.registers.latch_register(arg1, data)
            self.tick()

    def decode_and_execute_instruction(self):
        self.opcode = Opcode(self.data_path.read(self.instruction_counter)["opcode"])
        self.args = self.data_path.read(self.instruction_counter)["args"]
        opcode = self.opcode
        args = self.args
        self.tick()
        if opcode in (Opcode.ADD, Opcode.SUB, Opcode.MOD):
            self.data_path.registers.latch_register(
                args[0],
                self.execute_arithmetic(
                    opcode, self.data_path.registers.get_register(args[1]),
                    self.data_path.registers.get_register(args[2])
                ),
            )

        elif opcode in (Opcode.LOAD, Opcode.STORE):
            self.execute_memory(opcode, *args)
        elif opcode in (Opcode.IN, Opcode.OUT, Opcode.OUTN):
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

    def __repr__(self):
        """Вернуть строковое представление состояния процессора."""
        return (
                (
                        f"Tick: {self.ticks:3} PC: {self.instruction_counter:3} "
                        + " ".join([f"R{i}: {r:3}" for i, r in enumerate(self.data_path.registers.registers)])
                )
                + " Zero: "
                + str(self.data_path.alu.zero_flag)
                + " "
                + self.opcode
                + " "
                + str(self.args)
        )


def simulation(code, input_, data_memory_size, limit):
    data_path = DataPath(code, data_memory_size, input_)
    control_unit = ControlUnit(data_path)
    while control_unit.instruction_counter < len(code) and control_unit.ticks < limit:
        try:
            control_unit.decode_and_execute_instruction()
            logging.debug(control_unit)
        except StopIteration:
            logging.warning("HALT")
            break
        control_unit.latch_pc(control_unit.instruction_counter + 1)
    return data_path.port_manager.output_buffer, control_unit.instruction_counter, control_unit.ticks


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
            200,
            20000,
        )
        print("".join(output))
        print("instr_counter: ", instr_counter, "ticks:", ticks)
        logging.debug("output buffer: " + "".join(output))
        logging.debug("instr_counter: " + str(instr_counter) + " ticks: " + str(ticks))


if __name__ == "__main__":
    logging.getLogger().setLevel(logging.DEBUG)
    assert len(sys.argv) == 3, "Wrong arguments: machine.py <code_file> <input_file>"
    _, code_file, input_file = sys.argv
    main(code_file, input_file)
