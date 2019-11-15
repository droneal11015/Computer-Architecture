"""CPU functionality."""

import sys

HLT = 0b00000001
LDI = 0b10000010
PRN = 0b01000111
MUL = 0b10100010
PSH = 0b01000101
POP = 0b01000110
CALL = 0b01010000
RET = 0b00010001
ADD = 0b10100000
AND = 0b10101000
CMP = 0b10100111
DEC = 0b01100110
DIV = 0b10100011
INC = 0b01100101
IRET = 0b00010011
JEQ = 0b01010101
JLE = 0b01011001
JLT = 0b01011000
JMP = 0b01010100
JNE = 0b01010110
LD = 0b10000011
OR = 0b10101010
PRA = 0b01001000
SHL = 0b10101100
ST = 0b10000100
SUB = 0b10100001
XOR = 0b10101011

# flags
LT = 0b100
GT = 0b010
EQ = 0b001


class CPU:
    """Main CPU class."""

    def __init__(self):
        """Construct a new CPU."""
        # set up program counter
        self.pc = 0
        # set space for ram
        self.ram = [0] * 256
        # set space for the register
        self.reg = [0] * 8
        # set check for halted state
        self.halted = False
        # declare stack pointer
        self.SP = 7
        # initialize stack at address f4 (empty stack), as described in spec
        self.reg[self.SP] = 0xf4

        # hold a boolean for if an instruction sets the pc or not
        self.setsPC = False

        # set state for flags
        self.fl = 0

        # allow interrupts
        # self.iretOk = 1

        # set up branch table to hold operations pointing to handler defs
        self.branchtable = {
            HLT: self.hlt,
            LDI: self.ldi,
            PRN: self.prn,
            MUL: self.mul,
            POP: self.pop,
            PSH: self.psh,
            CALL: self.call,
            RET: self.ret,
            ADD: self.add,
            AND: self.andd,
            CMP: self.cmp,
            DEC: self.dec,
            DIV: self.div,
            INC: self.inc,
            # IRET: self.iret,
            JEQ: self.jeq,
            # JLE: self.jle,
            # JLT: self.jlt,
            JMP: self.jmp,
            JNE: self.jne,
            # LD: self.ld,
            OR: self.orr,
            # PRA: self.pra,
            SHL: self.shl,
            # ST: self.st,
            SUB: self.sub,
            XOR: self.xor,
        }

    # mar = memory address register
    # mdr = memory data register

    def ram_read(self, mar):
        return self.ram[mar]

    def ram_write(self, mdr, mar):
        self.ram[mar] = mdr

    def load(self, program):
        """Load a program into memory."""

        address = 0

        with open(program) as file:
            for line in file:
                line = line.split("#")[0]
                line = line.strip()

                if line == '':
                    continue

                val = int(line, 2)

                self.ram[address] = val
                address += 1

    def alu(self, op, reg_a, reg_b):
        """ALU operations."""

        if op == "ADD":
            self.reg[reg_a] += self.reg[reg_b]
        elif op == "AND":
            self.reg[reg_a] &= self.reg[reg_b]
        elif op == "SUB":
            self.reg[reg_a] -= self.reg[reg_b]
        elif op == "MUL":
            self.reg[reg_a] *= self.reg[reg_b]
        elif op == "DIV":
            self.reg[reg_a] /= self.reg[reg_b]
        elif op == "DEC":
            self.reg[reg_a] -= 1
        elif op == "INC":
            self.reg[reg_a] += 1
        elif op == "CMP":
            # clear all flags
            self.fl &= 0x11111000
            if self.reg[reg_a] < self.reg[reg_b]:
                self.fl |= LT
            elif self.reg[reg_a] > self.reg[reg_b]:
                self.fl |= GT
            else:
                self.fl |= EQ
        elif op == "OR":
            self.reg[reg_a] |= self.reg[reg_b]
        elif op == "SHL":
            self.reg[reg_a] <<= self.reg[reg_b]
        elif op == "XOR":
            self.reg[reg_a] ^= self.reg[reg_b]
        else:
            raise Exception("Unsupported ALU operation")

    def trace(self):
        """
        Handy function to print out the CPU state. You might want to call this
        from run() if you need help debugging.
        """

        print(f"TRACE: %02X | %02X %02X %02X |" % (
            self.pc,
            # self.fl,
            # self.ie,
            self.ram_read(self.pc),
            self.ram_read(self.pc + 1),
            self.ram_read(self.pc + 2)
        ), end='')

        for i in range(8):
            print(" %02X" % self.reg[i], end='')

        print()

    def run(self):
        """Run the CPU."""
        # while loop to check halted state
        while not self.halted:
            # check ram space
            ir = self.ram[self.pc]
            # add in alu ops
            operand_a = self.ram_read(self.pc + 1)
            operand_b = self.ram_read(self.pc + 2)

            fndInst = ((ir >> 6) & 0b11) + 1
            # add if the instruction sets the pc or not
            # and shift the code for the instruction
            self.setsPC = ((ir >> 4) & 0b1) == 1

            if ir in self.branchtable:
                self.branchtable[ir](operand_a, operand_b)

            else:
                # self.trace()
                print(
                    f"Invalid instruction {hex(ir)} at address {hex(self.pc)}")

            # if the instruction did not set the PC, move to next instruction
            if not self.setsPC:
                self.pc += fndInst

    def ldi(self, operand_a, operand_b):
        self.reg[operand_a] = operand_b

    def prn(self, operand_a, operand_b):
        print(self.reg[operand_a])

    def pshVal(self, val):
        self.reg[self.SP] -= 1
        self.ram_write(val, self.reg[self.SP])

    def psh(self, operand_a, operand_b):
        self.pshVal(self.reg[operand_a])

    def popVal(self):
        val = self.ram_read(self.reg[self.SP])
        self.reg[self.SP] += 1
        return val

    def pop(self, operand_a, operand_b):
        self.reg[operand_a] = self.popVal()

    def call(self, operand_a, operand_b):
        self.pshVal(self.pc + 2)
        self.pc = self.reg[operand_a]

    def ret(self, operand_a, operand_b):
        self.pc = self.popVal()

    # Jump
    def jmp(self, operand_a, operand_b):
        self.pc = self.reg[operand_a]

    # JEQ
    def jeq(self, operand_a, operand_b):
        if self.fl & EQ:
            self.pc = self.reg[operand_a]
        else:
            self.setsPC = False

    # JNE
    def jne(self, operand_a, operand_b):
        if not self.fl & EQ:
            self.pc = self.reg[operand_a]
        else:
            self.setsPC = False

    def hlt(self, operand_a, operand_b):
        self.halted = True

    # def iret(self, operand_a, operand_b):
    #     # resume stack work
    #     for i in range(6, -1, -1):
    #         self.reg[i] = self.popVal()
    #     self.fl = self.popVal()
    #     self.pc = self.popVal()
    #     # allow interrupts
    #     self.iretOK = 1

    # AlU opperations

    def add(self, operand_a, operand_b):
        self.alu("ADD", operand_a, operand_b)

    def andd(self, operand_a, operand_b):
        self.alu("AND", operand_a, operand_b)

    def sub(self, operand_a, operand_b):
        self.alu("SUB", operand_a, operand_b)

    def mul(self, operand_a, operand_b):
        self.alu("MUL", operand_a, operand_b)

    def div(self, operand_a, operand_b):
        self.alu("DIV", operand_a, operand_b)

    def dec(self, operand_a, operand_b):
        self.alu("DEC", operand_a, None)

    def inc(self, operand_a, operand_b):
        self.alu("INC", operand_a, None)

    def orr(self, operand_a, operand_b):
        self.alu("OR", operand_a, operand_b)

    def xor(self, operand_a, operand_b):
        self.alu("XOR", operand_a, operand_b)

    def cmp(self, operand_a, operand_b):
        self.alu("CMP", operand_a, operand_b)

    def shl(self, operand_a, operand_b):
        self.alu("SHL", operand_a, operand_b)