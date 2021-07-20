import error, config

nextvariableidentifier = 0
freepointers: list[int] = range(config.config["ram"])[1:]
usedvariablepointers: list[int] = []
maxvariables = 64
maxregs = config.config["regs"]
usednames: list[str] = ["+", "//", "*", "^", "&", "|", "-", "num", "function", "object", "=", "==", ">=", "<=", "!=", ">", "<", "none", "array", "->", "{", "}", "\"", "[", "]", ",", "(", ")", "$", ".", ";", "%"]

def getvariablefreepointer(width: int) -> int:
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

def getvariableidentifier() -> int:
    global nextvariableidentifier

    nextvariableidentifier += 1
    return nextvariableidentifier

class Var:
    def __init__(self, name: str, type: str, width: int, at_zero = False):
        self.name = name
        self.type = type
        self.width = width
        self.identifier = getvariableidentifier()
        
        if not at_zero:
            self.pointer = getvariablefreepointer(width)
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
