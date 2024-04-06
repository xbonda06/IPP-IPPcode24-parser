# IPPcode24 Parser

This is the description of the script parse.py (`readme1.pdf` czech variant) , which has been developed as part of the first task of the IPP course at VUT FIT in the academic year 2023/2024. This script provides lexical and semantic analysis of the IPPcode24 language and generates an XML file representing this code.

#### Score: 6.2 / 7

## Parse.py description

The parse.py script reads the source code in the IPPcode24 language from the standard input line by line. It processes received instructions and adds them to the XML file.

The source code is analyzed in a loop, which is part of the main Parser class. The loop removes comments, spaces, and whitespace characters, which it ignores. Each instruction is numbered using the order attribute, which stores information about the line being analyzed.

At the beginning of the loop, it checks if the first line is ".IPPcode24". If yes, it initializes the XML file. Each subsequent instruction is processed sequentially, verifying its existence, type, correctness of arguments, and properly adding it to the XML file. I used The ElementTree XML API and Minimal DOM modules for working with the XML file.

To simplify the analysis, lists of instructions supported by IPPcode24 and special lists of different types of instructions based on the number and type of arguments are created. I also created lists of allowed argument types and memory frames. These lists are used by individual classes to check the correct number and type of arguments.

The script is created according to the principles of OOP and contains several classes, which have defined roles and communicate with each other. The entire functionality of the program is ensured by the methods of these classes:

- **ProgramIOController:** Processes the input parameters of the script and provides help or displays error messages.
- **Instruction:** Represents a single IPPcode24 instruction, including its order, operation code, and arguments.
- **Argument:** Stores information about a single instruction argument, including its type and value.
- **InstructionValidator:** Performs syntactic and lexical analysis of instructions and verifies the correctness of arguments.
- **Parser:** Ensures the main logic of processing the input code and its conversion to XML.
- **XMLGenerator:** Class for generating the output XML document.
