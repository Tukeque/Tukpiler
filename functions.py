import error, config

nextvariableidentifier = 0
freepointers: list[int] = range(config.config["ram"])[1:]
usedvariablepointers: list[int] = []
maxvariables = 64
maxregs = config.config["regs"]
usednames: list[str] = ["+", "//", "*", "^", "&", "|", "-", "num", "function", "object", "=", "==", ">=", "<=", "!=", ">", "<", "none", "array", "->", "{", "}", "\"", "[", "]", ",", "(", ")", "$", ".", ";", "%", "[", "]", "if", "else", "elif", "while", "switch"]
types = ["num", "none", "array"]

def get_variable_free_pointer(width: int) -> int:
    global usedvariablepointers

    for i in freepointers:
        can = True
        for j in range(width):
            if i+j in usedvariablepointers:
                can = False

        if can == True:
            for j in range(width):
                usedvariablepointers.append(i+j)
            return i

    error.error("exceeded the maximum amount of variables")
    return -1

def get_variable_identifier() -> int:
    global nextvariableidentifier

    nextvariableidentifier += 1
    return nextvariableidentifier

class Var:
    def __init__(self, name: str, type: str, width: int, at_zero = False, argument = False, reg: str = ""):
        self.name = name
        self.type = type
        self.width = width
        self.identifier = get_variable_identifier()
        
        if not at_zero and argument == False:
            self.pointer = f"{'M' if config.config['modfix'] == True else '#'}{get_variable_free_pointer(width)}"
        elif argument == True:
            self.pointer = reg
        else:
            self.pointer = 0

    def print(self):
        print(f"{self.type} variable at address {self.pointer}, with {self.width} and identifier {self.identifier}")

usedregs = [0] # reg 0 doesn't count
def get_reg() -> str:
    for i in range(maxregs):
        if i not in usedregs:
            usedregs.append(i)
            return f"R{i}"

def free_reg(reg: str):
    usedregs.remove(int(reg[1:]))

nextfuncidentifier = 0
func_names: list[str] = []
def get_function_identifier() -> int:
    global nextfuncidentifier

    nextfuncidentifier += 1
    return nextfuncidentifier

class Func():
    def __init__(self, name, args, return_type):
        global func_names

        self.name = name
        self.args = args
        self.return_type = return_type
        self.identifier = get_function_identifier()
        if name in func_names:
            error.error(f"tried to create a function that already exists({name})")
        else:
            func_names.append(name)

    def print(self):
        print(f"function {self.name} with identifier {self.identifier}, args {self.args} and return type {self.return_type}")