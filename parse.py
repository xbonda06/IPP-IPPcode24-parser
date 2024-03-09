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
instructions_w_two_vs = ["MOVE", "INT2CHAR", "STRLEN", "TYPE", "NOT"]  # var symb
instructions_w_two_vt = ["READ"]  # var type
instructions_w_three_vss = ["ADD", "SUB", "MUL", "IDIV", "LT", "GT", "EQ", "AND", "OR",
                            "STRI2INT", "CONCAT", "GETCHAR", "SETCHAR"]  # var symb symb
instructions_w_three_lss = ["JUMPIFEQ", "JUMPIFNEQ"]  # label symb symb

arguments_type_list = ["int", "bool", "string", "nil", "label", "type", "var"]
argument_frames = ["GF", "LF", "TF"]


# Class for controlling the program input and output
# It checks the number of arguments and displays help and error messages
class ProgramIOController:
    def __init__(self, allowed_args=None):
        self.allowed_args = allowed_args or []

    def check_args(self):
        if len(sys.argv) > 1:
            if sys.argv[1] == '--help':
                self.display_help()
            elif sys.argv[1] not in self.allowed_args:
                self.error_exit("Invalid number of arguments", 10)

    @staticmethod
    def display_help():
        help_message = """
        This script reads the source code in IPPcode24 from stdin.
        It creates an XML file from it, which it prints to stdout.

        Optional parameters:
        --help - prints this help message
        """
        print(help_message)
        sys.exit(0)

    @staticmethod
    def error_exit(message, code):
        print(message, file=sys.stderr)
        sys.exit(code)


# Class for storing the instruction and its arguments
class Instruction:
    def __init__(self, order, opcode, args):
        if opcode not in instructions_list:
            ProgramIOController.error_exit(f"Error: unknown instruction {opcode}", 22)
        self.order = order
        self.opcode = opcode
        self.args = args


# Class for storing the argument
# It checks the validity of the argument type and value
class Argument:
    def __init__(self, arg_type, arg_value):
        self.type = ""
        self.value = arg_value
        self.process_type(arg_type, arg_value)
        self.process_value(self.type, arg_value)
        if arg_type in argument_frames:
            self.value = f"{arg_type}@{arg_value}"  # add frame to value GF@var
        else:
            self.value = arg_value

    def process_type(self, arg_type, arg_value):
        if any(c.isupper() for c in arg_type) and arg_type not in argument_frames:
            ProgramIOController.error_exit("Error: invalid argument type", 23)
        else:
            self.type = arg_type if arg_type in arguments_type_list else "var"
        if arg_type == "bool" and arg_value not in ["true", "false"]:
            ProgramIOController.error_exit("Error: invalid value of argument", 23)
        if arg_type == "nil" and arg_value != "nil":
            ProgramIOController.error_exit("Error: invalid value of argument", 23)

    @staticmethod
    def parse_string_on_esc_seq(string):
        pattern = r'\\(?!([0-9]{3}))'  # check if every escape sequence contains 3 digits
        if re.search(pattern, string):
            ProgramIOController.error_exit("Error: invalid value of argument", 23)

    def process_value(self, arg_type, arg_value):
        special_chars = ["_", "-", "$", "&", "%", "*", "!", "?"]  # allowed special characters in identifiers
        # integer value cannot be empty
        if arg_type == "int" and len(arg_value) == 0:
            ProgramIOController.error_exit("Error: invalid value of argument", 23)
        # integer value contains only digits and can start with + or -
        if arg_type == "int" and \
                (not arg_value.isdigit() and not arg_value[0] in ["+", "-"] and not arg_value[1:].isdigit()):
            ProgramIOController.error_exit("Error: invalid value of argument", 23)
        if arg_type in ["label", "var"]:
            if not arg_value[0].isalpha() and arg_value[0] not in special_chars:
                ProgramIOController.error_exit("Error: invalid value of argument", 23)
            for char in arg_value:
                if not char.isalnum() and char not in special_chars:
                    ProgramIOController.error_exit("Error: invalid value of argument", 23)
        if arg_type == "string":
            self.parse_string_on_esc_seq(arg_value)
            arg_value.replace("<", "&lt;")
            arg_value.replace(">", "&gt;")
            arg_value.replace("&", "&amp;")


# Class for validating the instruction
# It checks the number of arguments and their types
class InstructionValidator:
    def __init__(self, instruction):
        self.instruction = instruction

    def validate(self):
        if self.instruction.opcode in instructions_w_no_args:
            if len(self.instruction.args) != 0:
                ProgramIOController.error_exit(f"Error: {self.instruction.opcode} takes no arguments", 23)
        elif self.instruction.opcode in instructions_w_one_label:
            if len(self.instruction.args) != 1 or self.instruction.args[0].type != "label":
                ProgramIOController.error_exit(f"Error: {self.instruction.opcode} takes one label", 23)
        elif self.instruction.opcode in instructions_w_one_symb:
            if len(self.instruction.args) != 1 or self.instruction.args[0].type not in ["var", "string", "int", "bool",
                                                                                        "nil"]:
                ProgramIOController.error_exit(f"Error: {self.instruction.opcode} takes one symbol", 23)
        elif self.instruction.opcode in instructions_w_one_var:
            if len(self.instruction.args) != 1 or self.instruction.args[0].type != "var":
                ProgramIOController.error_exit(f"Error: {self.instruction.opcode} takes one variable", 23)
        elif self.instruction.opcode in instructions_w_two_vs:
            if len(self.instruction.args) != 2 or self.instruction.args[0].type != "var" or \
                    self.instruction.args[1].type not in arguments_type_list:
                ProgramIOController.error_exit(f"Error: {self.instruction.opcode} takes two symbols", 23)
        elif self.instruction.opcode in instructions_w_two_vt:
            if len(self.instruction.args) != 2 or self.instruction.args[0].type != "var" or \
                    self.instruction.args[1].value not in ["int", "string", "bool"]:
                ProgramIOController.error_exit(f"Error: {self.instruction.opcode} takes two symbols", 23)
        elif self.instruction.opcode in instructions_w_three_vss:
            if len(self.instruction.args) != 3 or \
                    self.instruction.args[0].type != "var" or \
                    self.instruction.args[1].type not in arguments_type_list or \
                    self.instruction.args[2].type not in arguments_type_list:
                ProgramIOController.error_exit(f"Error: {self.instruction.opcode} takes three symbols", 23)
        elif self.instruction.opcode in instructions_w_three_lss:
            if len(self.instruction.args) != 3 or \
                    self.instruction.args[0].type != "label" or \
                    self.instruction.args[1].type not in arguments_type_list or \
                    self.instruction.args[2].type not in arguments_type_list:
                ProgramIOController.error_exit(f"Error: {self.instruction.opcode} takes three symbols", 23)

        match self.instruction.opcode:
            case "ADD", "SUB", "MUL", "IDIV":
                if self.instruction.args[1].type != "int" and self.instruction.args[2].type != "int":
                    ProgramIOController.error_exit(f"Error: invalid type of argument", 23)
            case "LT", "GT", "EQ", "JUMPIFEQ", "JUMPIFNEQ":
                allowed_types = ["bool", "int", "string", "var"]
                if self.instruction.opcode in ["EQ", "JUMPIFEQ", "JUMPIFNEQ"]:
                    allowed_types.append("nil")
                if self.instruction.args[1].type not in allowed_types or self.instruction.args[
                    2].type not in allowed_types:
                    ProgramIOController.error_exit(f"Error: invalid type of argument", 23)
                if self.instruction.args[1].type != "var" and self.instruction.args[2].type != "var" and \
                        self.instruction.args[1].type != self.instruction.args[2].type:
                    ProgramIOController.error_exit(f"Error: invalid type of argument", 23)
            case "AND", "OR":
                if self.instruction.args[1].type not in ["bool", "var"] or self.instruction.args[2].type not in ["bool",
                                                                                                                 "var"]:
                    ProgramIOController.error_exit(f"Error: invalid type of argument", 23)
            case "NOT":
                if self.instruction.args[1].type not in ["bool", "var"] or self.instruction.args[0].type != "var":
                    ProgramIOController.error_exit(f"Error: invalid type of argument", 23)
            case "INT2CHAR":
                if self.instruction.args[1].type not in ["int", "var"]:
                    ProgramIOController.error_exit(f"Error: invalid type of argument", 23)
            case "STRI2INT", "GETCHAR":
                if self.instruction.args[1].type not in ["string", "var"]:
                    ProgramIOController.error_exit(f"Error: invalid type of argument", 23)
            case "CONCAT":
                if self.instruction.args[1].type not in ["string", "var"]:
                    ProgramIOController.error_exit(f"Error: invalid type of argument", 23)
                if self.instruction.args[2].type not in ["string", "var"]:
                    ProgramIOController.error_exit(f"Error: invalid type of argument", 23)
            case "STRLEN":
                if self.instruction.args[1].type not in ["string", "var"]:
                    ProgramIOController.error_exit(f"Error: invalid type of argument", 23)
            case "SETCHAR":
                if self.instruction.args[1].type not in ["int", "var"] or \
                        self.instruction.args[2].type not in ["string", "var"]:
                    ProgramIOController.error_exit(f"Error: invalid type of argument", 23)
            case "DPRINT":
                if self.instruction.args[0].type not in arguments_type_list:
                    ProgramIOController.error_exit(f"Error: invalid type of argument", 23)


# The main class of the program for parsing the source code and formatting instructions to XML
class Parser:
    def __init__(self):
        self.order = 0
        self.header_checked = False
        self.xml_gen = XMLGenerator()

    def process_line(self, line):
        if line.strip().startswith(".IPPcode24") and self.header_checked:
            ProgramIOController.error_exit("Error: header found twice", 23)
        elif line.strip().startswith(".IPPcode24") and not self.header_checked:
            self.check_header(line)
        elif line.strip().startswith("#") or line.strip() == "":
            return
        elif not self.header_checked:
            ProgramIOController.error_exit("Error: header not found", 21)
        else:
            self.order += 1
            instruction = self.get_instruction_from_line(line)
            if instruction is not None:
                self.validate_and_generate(instruction)

    def check_header(self, line):
        line_parts = line.split()
        line_without_comments = line_parts[0].split("#")
        if line_without_comments[0] != ".IPPcode24":
            ProgramIOController.error_exit("Error: invalid header", 21)
        self.header_checked = True

    def get_instruction_from_line(self, line):
        line_without_comment = line.split("#", 1)
        if len(line_without_comment) > 1:
            line = line_without_comment[0]
        parts_of_line = line.strip().split(maxsplit=1)
        opcode = parts_of_line[0].upper()

        if len(parts_of_line) > 1:
            instruction_args = parts_of_line[1]
        else:
            instruction_args = ""
        args = self.parse_arg(opcode, instruction_args)
        return Instruction(self.order, opcode, args)

    @staticmethod
    def parse_arg(opcode, instruction_args):
        args = []
        arg_type, arg_value = "", ""
        for arg in instruction_args.split():
            if '@' in arg:
                if arg.count("@") > 1:
                    ProgramIOController.error_exit("Error: invalid argument", 23)
                arg_type, arg_value = arg.split('@', 1)
            elif arg in arguments_type_list and opcode in instructions_w_two_vt:
                arg_type = "type"
                arg_value = arg
            else:
                if (opcode in instructions_w_one_label or opcode in instructions_w_three_lss) and args == []:
                    arg_type = "label"
                    arg_value = arg
                else:
                    ProgramIOController.error_exit(f"Error: invalid argument", 23)
            args.append(Argument(arg_type, arg_value))
        return args

    def validate_and_generate(self, instruction):
        validator = InstructionValidator(instruction)
        validator.validate()
        self.xml_gen.create_xml_instruction(instruction)

    def parse(self):
        for line in sys.stdin:
            self.process_line(line)


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


def main():
    ProgramIOController(["--help"]).check_args()
    parser = Parser()
    parser.parse()
    xml_str = parser.xml_gen.get_xml()
    sys.stdout.buffer.write(xml_str)


if __name__ == "__main__":
    main()
