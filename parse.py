import re
import sys
import xml.etree.ElementTree as ET
from xml.dom import minidom

instructions_list = ["MOVE", "CREATEFRAME", "PUSHFRAME", "POPFRAME", "DEFVAR", "CALL",
                     "RETURN", "PUSHS", "POPS", "ADD", "SUB", "MUL", "IDIV", "LT", "GT",
                     "EQ", "AND", "OR", "NOT", "INT2CHAR", "STRI2INT", "READ", "WRITE",
                     "CONCAT", "STRLEN", "GETCHAR", "SETCHAR", "TYPE", "LABEL", "JUMP",
                     "JUMPIFEQ", "JUMPIFNEQ", "DPRINT", "BREAK", "EXIT"]

instructions_w_no_args = ["CREATEFRAME", "PUSHFRAME", "POPFRAME", "RETURN", "BREAK"]
instructions_w_one_label = ["CALL", "LABEL", "JUMP"]
instructions_w_one_symb = ["PUSHS", "WRITE", "DPRINT", "EXIT"]
instructions_w_one_var = ["DEFVAR", "POPS"]
instructions_w_two_vs = ["MOVE", "INT2CHAR", "STRLEN", "TYPE", "NOT"]
instructions_w_two_vt = ["READ"]
instructions_w_three_vss = ["ADD", "SUB", "MUL", "IDIV", "LT", "GT", "EQ", "AND", "OR",
                            "STRI2INT", "CONCAT", "GETCHAR", "SETCHAR"]
instructions_w_three_lss = ["JUMPIFEQ", "JUMPIFNEQ"]

arguments_type_list = ["int", "bool", "string", "nil", "label", "type", "var"]
argument_frames = ["GF", "LF", "TF"]


def contains_uppercase(s):
    return any(c.isupper() for c in s)


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


def check_arg_type(arg_type, arg_value):
    if contains_uppercase(arg_type) and arg_type not in argument_frames:
        print("Error: invalid argument type", file=sys.stderr)
        sys.exit(23)
    if arg_type == "bool" and arg_value not in ["true", "false"]:
        print("Error: invalid value of argument", file=sys.stderr)
        sys.exit(23)
    if arg_type == "nil" and arg_value != "nil":
        print("Error: invalid value of argument", file=sys.stderr)
        sys.exit(23)


def parse_string(string):
    pattern = r'\\(?!([0-9]{3}))'
    if re.search(pattern, string):
        print("Error: invalid escape sequence", file=sys.stderr)
        sys.exit(23)


def check_arg_value(arg_type, arg_value):
    special_chars = ["_", "-", "$", "&", "%", "*", "!", "?"]
    if arg_type == "int" and len(arg_value) == 0:
        print("Error: invalid value of argument", file=sys.stderr)
        sys.exit(23)
    if arg_type == "int" and \
            (not arg_value.isdigit() and not arg_value[0] in ["+", "-"] and not arg_value[1:].isdigit()):
        print("Error: invalid value of argument", file=sys.stderr)
        sys.exit(23)
    if arg_type in ["label", "var"]:
        if not arg_value[0].isalpha() and arg_value[0] not in special_chars:
            print("Error: invalid value of argument", file=sys.stderr)
            sys.exit(23)
        for char in arg_value:
            if not char.isalnum() and char not in special_chars:
                print("Error: invalid value of argument", file=sys.stderr)
                sys.exit(23)
    if arg_type == "string":
        parse_string(arg_value)


class Argument:
    def __init__(self, arg_type, arg_value):
        check_arg_type(arg_type, arg_value)
        self.type = arg_type if arg_type in arguments_type_list else "var"
        check_arg_value(self.type, arg_value)
        arg_value.replace("<", "&lt;")
        arg_value.replace(">", "&gt;")
        arg_value.replace("&", "&amp;")
        if arg_type in argument_frames:
            self.value = f"{arg_type}@{arg_value}"
        else:
            self.value = arg_value


class XMLGenerator:
    def __init__(self):
        self.root = ET.Element("program", language="IPPcode24")

    def create_xml_instruction(self, instruction):
        xml_instruction = ET.Element("instruction", order=str(instruction.order), opcode=instruction.opcode)
        if not instruction.args:
            xml_instruction.text = '\n    '
        else:
            for i, arg in enumerate(instruction.args, start=1):
                arg_elem = ET.SubElement(xml_instruction, f"arg{i}", type=arg.type)
                arg_elem.text = arg.value
        self.root.append(xml_instruction)

    def get_xml(self):
        xml_str = ET.tostring(self.root, encoding="utf-8", method="xml", xml_declaration=True)
        xml_str = minidom.parseString(xml_str).toprettyxml(indent="    ").encode("utf-8")
        xml_str = xml_str.replace(b"<?xml version=\"1.0\" ?>\n", b"<?xml version=\"1.0\" encoding=\"UTF-8\"?>\n")
        return xml_str


def parse_arg(opcode, instruction_args):
    args = []
    for arg in instruction_args.split():
        if '@' in arg:
            if arg.count("@") > 1:
                print("Error: invalid argument", file=sys.stderr)
                sys.exit(23)
            arg_type, arg_value = arg.split('@', 1)
        elif arg in arguments_type_list and opcode in instructions_w_two_vt:
            arg_type = "type"
            arg_value = arg
        else:
            if (opcode in instructions_w_one_label or opcode in instructions_w_three_lss) and args == []:
                arg_type = "label"
                arg_value = arg
            else:
                sys.exit(23)
        args.append(Argument(arg_type, arg_value))
    return args


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
    args = parse_arg(opcode, instruction_args)
    return Instruction(line_number, opcode, args)


def parse_instructions(instruction):
    if instruction.opcode in instructions_w_no_args:
        if len(instruction.args) != 0:
            print(f"Error: {instruction.opcode} takes no arguments", file=sys.stderr)
            sys.exit(23)
    elif instruction.opcode in instructions_w_one_label:
        if len(instruction.args) != 1 or instruction.args[0].type != "label":
            print(f"Error: {instruction.opcode} takes one label", file=sys.stderr)
            sys.exit(23)
    elif instruction.opcode in instructions_w_one_symb:
        if len(instruction.args) != 1 or instruction.args[0].type not in ["var", "string", "int", "bool", "nil"] and \
                instruction.args[0].type not in argument_frames:
            print(f"Error: {instruction.opcode} takes one symbol", file=sys.stderr)
            sys.exit(23)
    elif instruction.opcode in instructions_w_one_var:
        if len(instruction.args) != 1 or instruction.args[0].type != "var":
            print(f"Error: {instruction.opcode} takes one variable", file=sys.stderr)
            sys.exit(23)
    elif instruction.opcode in instructions_w_two_vs:
        if len(instruction.args) != 2 or instruction.args[0].type != "var" or \
                instruction.args[1].type not in arguments_type_list:
            print(f"Error: {instruction.opcode} takes two variables", file=sys.stderr)
            sys.exit(23)
    elif instruction.opcode in instructions_w_two_vt:
        if len(instruction.args) != 2 or instruction.args[0].type != "var" or \
                instruction.args[1].value not in ["int", "string", "bool"] and instruction.args[1].value != "":
            print(f"Error: {instruction.opcode} takes two variables", file=sys.stderr)
            sys.exit(23)
    elif instruction.opcode in instructions_w_three_vss:
        if len(instruction.args) != 3 or \
                instruction.args[0].type != "var" or \
                instruction.args[1].type not in arguments_type_list or \
                instruction.args[2].type not in arguments_type_list:
            print(f"Error: {instruction.opcode} takes three symbols", file=sys.stderr)
            sys.exit(23)
    elif instruction.opcode in instructions_w_three_lss:
        if len(instruction.args) != 3 or \
                instruction.args[0].type != "label" or \
                instruction.args[1].type not in arguments_type_list or \
                instruction.args[2].type not in arguments_type_list:
            print(f"Error: {instruction.opcode} takes three symbols", file=sys.stderr)
            sys.exit(23)

    match instruction.opcode:
        case "ADD", "SUB", "MUL", "IDIV":
            if instruction.args[0].type != "var" and \
                    instruction.args[1].type != "int" and \
                    instruction.args[2].type != "int":
                print("Error: invalid type of argument", file=sys.stderr)
                sys.exit(23)
        case "LT", "GT", "EQ", "JUMPIFEQ", "JUMPIFNEQ":
            allowed_types = ["bool", "int", "string", "var"]
            if instruction.opcode in ["EQ", "JUMPIFEQ", "JUMPIFNEQ"]:
                allowed_types.append("nil")
            if instruction.args[0].type != "var" or instruction.args[1].type not in allowed_types or \
                    instruction.args[2].type not in allowed_types:
                print("Error: invalid type of argument", file=sys.stderr)
                sys.exit(23)
            if instruction.args[1].type != "var" and instruction.args[2].type != "var" and \
                    instruction.args[1].type != instruction.args[2].type:
                print("Error: invalid type of argument", file=sys.stderr)
                sys.exit(23)
        case "AND", "OR":
            if instruction.args[0].type != "var" or \
                    instruction.args[1].type not in ["bool", "var"] or \
                    instruction.args[2].type not in ["bool", "var"]:
                print("Error: invalid type of argument", file=sys.stderr)
                sys.exit(23)
        case "NOT":
            if instruction.args[1].type not in ["bool", "var"] or instruction.args[0].type != "var":
                print("Error: invalid type of argument", file=sys.stderr)
                sys.exit(23)
        case "INT2CHAR":
            if instruction.args[0].type != "var" or instruction.args[1].type not in ["int", "var"]:
                print("Error: invalid type of argument", file=sys.stderr)
                sys.exit(23)
        case "STRI2INT", "GETCHAR":
            if instruction.args[0].type != "var" or instruction.args[1].type not in ["string", "var"]:
                print("Error: first argument must be var and second argument must be string or var", file=sys.stderr)
                sys.exit(23)
        case "CONCAT":
            if instruction.args[0].type != "var":
                print("Error: first argument must be of type var", file=sys.stderr)
                sys.exit(23)
            if instruction.args[1].type not in ["string", "var"]:
                print("Error: second argument must be either of type string or a variable", file=sys.stderr)
                sys.exit(23)
            if instruction.args[2].type not in ["string", "var"]:
                print("Error: third argument must be either of type string or a variable", file=sys.stderr)
                sys.exit(23)
        case "STRLEN":
            if instruction.args[0].type != "var" or instruction.args[1].type not in ["string", "var"]:
                print("Error: invalid type of argument", file=sys.stderr)
                sys.exit(23)
        case "SETCHAR":
            if instruction.args[0].type != "var" or instruction.args[1].type not in ["int", "var"] or \
                    instruction.args[2].type not in ["string", "var"]:
                print("Error: invalid type of argument", file=sys.stderr)
                sys.exit(23)
        case "DPRINT":
            if instruction.args[0].type not in arguments_type_list:
                print("Error: invalid type of argument", file=sys.stderr)
                sys.exit(23)


def main():
    arg_checker = ArgumentCheck(["parse.py", "--help"])
    arg_checker.check_args()

    xml_gen = XMLGenerator()

    line_number = 0
    header_checked = False
    for line in sys.stdin:
        if line.strip().startswith(".IPPcode24") and header_checked:
            print("Error: multiple headers found", file=sys.stderr)
            sys.exit(23)
        elif line.strip().startswith(".IPPcode24") and not header_checked:
            line_parts = line.split()
            line_without_comments = line_parts[0].split("#")
            if line_without_comments[0] != ".IPPcode24":
                print("Error: wrong header format", file=sys.stderr)
                sys.exit(21)
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
            parse_instructions(instruction)
            xml_gen.create_xml_instruction(instruction)

    xml_str = xml_gen.get_xml()
    sys.stdout.buffer.write(xml_str)


if __name__ == "__main__":
    main()
