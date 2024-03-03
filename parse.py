import sys
import xml.etree.ElementTree as ET
from xml.dom import minidom

instructions_list = ["MOVE", "CREATEFRAME", "PUSHFRAME", "POPFRAME", "DEFVAR", "CALL", "RETURN", "PUSHS", "POPS",
                        "ADD", "SUB", "MUL", "IDIV", "LT", "GT", "EQ", "AND", "OR", "NOT", "INT2CHAR", "STRI2INT",
                        "READ", "WRITE", "CONCAT", "STRLEN", "GETCHAR", "SETCHAR", "TYPE", "LABEL", "JUMP", "JUMPIFEQ",
                        "JUMPIFNEQ", "EXIT", "DPRINT", "BREAK"]

arguments_list = ["int", "bool", "string", "nil", "label", "type", "var"]


class ArgumentCheck:
    def __init__(self, expected_args=None):
        self.expected_args = expected_args or []

    def check_args(self):
        if len(sys.argv) > 1 and sys.argv[1] not in self.expected_args:
            print("Invalid number of arguments", file=sys.stderr)
            sys.exit(10)
        elif len(sys.argv) == 2 and sys.argv[1] in self.expected_args:
            print("HINT:")
            print("This script reads the source code in IPPcode24 from stdin.")
            print("It creates an XML file from it, which it prints to stdout.\n")
            print("Optional parameters:")
            print("--help - prints this help message\n")
            sys.exit(0)


class Instruction:
    def __init__(self, order, opcode, args):
        if opcode not in instructions_list:
            print(f"Error: unknown instruction {opcode}", file=sys.stderr)
            sys.exit(22)
        self.order = order
        self.opcode = opcode
        self.args = args


class Argument:
    def __init__(self, arg_type, arg_value):
        self.type = arg_type
        self.value = arg_value


class XMLGenerator:
    def __init__(self):
        self.root = ET.Element("program", language="IPPcode24")

    def create_xml_instruction(self, instruction):
        xml_instruction = ET.Element("instruction", order=str(instruction.order), opcode=instruction.opcode)
        for i, arg in enumerate(instruction.args, start=1):
            arg_elem = ET.SubElement(xml_instruction, f"arg{i}", type=arg.type)
            arg_elem.text = arg.value
        self.root.append(xml_instruction)

    def get_xml(self):
        xml_str = ET.tostring(self.root, encoding="utf-8", method="xml", xml_declaration=True)
        xml_str = minidom.parseString(xml_str).toprettyxml(indent="    ").encode("utf-8")
        return xml_str


def get_instruction_from_line(line, line_number):
    line_without_comment = line.split("#", 1)
    if len(line_without_comment) > 1:
        line = line_without_comment[0]
    parts_of_line = line.strip().split(maxsplit=1)
    opcode = parts_of_line[0].upper()

    if len(parts_of_line) > 1:
        instruction_args = parts_of_line[1]
    else:
        instruction_args = ""
    args = []
    for arg in instruction_args.split():
        if '@' in arg:
            arg_type, arg_value = arg.split('@', 1)
        else:
            arg_type = "label"
            arg_value = arg
        args.append(Argument(arg_type, arg_value))
    return Instruction(line_number, opcode, args)


def main():
    arg_checker = ArgumentCheck(["parse.py", "--help"])
    arg_checker.check_args()

    xml_gen = XMLGenerator()

    line_number = 0
    header_checked = False
    for line in sys.stdin:
        if line.strip().startswith(".IPPcode24"):
            header_checked = True
            continue
        elif line.strip().startswith("#") or line.strip() == "":
            continue
        if not header_checked:
            print("Error: header not found", file=sys.stderr)
            sys.exit(21)

        line_number += 1
        instruction = get_instruction_from_line(line, line_number)
        if instruction is not None:
            xml_gen.create_xml_instruction(instruction)

    xml_str = xml_gen.get_xml()
    sys.stdout.buffer.write(xml_str)


if __name__ == "__main__":
    main()
