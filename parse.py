import sys
import xml.etree.ElementTree as ET


class ArgumentCheck:
    def __init__(self, expected_args=None):
        self.expected_args = expected_args or []

    def check_args(self):
        if len(sys.argv) > 1 and sys.argv[1] not in self.expected_args:
            print("Invalid number of arguments")
            sys.exit(10)
        elif len(sys.argv) == 2 and sys.argv[1] in self.expected_args:
            print("HINT:")
            print("This script reads the source code in IPPcode24 from stdin.")
            print("It creates an XML file from it, which it prints to stdout.\n")
            print("Optional parameters:")
            print("--help - prints this help message\n")
            print("Usage:")
            sys.exit(0)


def main():
    arg_checker = ArgumentCheck(["parse.py", "--help"])
    arg_checker.check_args()

    root = ET.Element("program", language="IPPcode24")

    xml_str = ET.tostring(root, encoding="utf-8", method="xml", xml_declaration=True)

    sys.stdout.buffer.write(xml_str)

if __name__ == "__main__":
    main()
