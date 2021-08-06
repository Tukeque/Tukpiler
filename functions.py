import error, config, compiler

nextvariableidentifier = 0
freepointers: list[int] = range(config.config["ram"])[1:]
usedvariablepointers: list[int] = []
maxvariables = 64
maxregs = config.config["regs"]
usednames: list[str] = ["+", "//", "*", "^", "&", "|", "-", "num", "function", "object", "=", "==", ">=", "<=", "!=", ">", "<", "none", "array", "->", "{", "}", "\"", "[", "]", ",", "(", ")", "$", ".", ";", "%", "[", "]", "if", "else", "elif", "while", "switch"]
types = ["num", "none", "array"]
type_to_width = {
    "num": 1,
    "array": -1, # width is variable depending on length of array
    "none": 1
}

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
    def __init__(self, name: str, type: str, width: int, at_zero = False, argument = False, reg: str = "", in_reg: bool = False):
        self.name = name
        self.type = type
        self.width = width
        self.identifier = get_variable_identifier()
        
        if not at_zero and argument == False:
            self.pointer = f"{'M' if config.config['modfix'] == True else '#'}{get_variable_free_pointer(width)}"
        elif argument == True:
            self.pointer = reg
        elif in_reg == True:
            self.pointer = get_reg()
        else:
            self.pointer = 0

        self.in_reg = in_reg

    def get(self, urcl: list[str]) -> str:
        if not self.in_reg:
            reg = get_reg()
            urcl.append(f"LOD {reg} {self.pointer}")
            return reg
        else:
            return self.pointer

    def set(self, x, urcl: list[str]):
        if x == self.name: return
        x_var = compiler.vars[x]

        op = ""
        if x_var.in_reg and self.in_reg: # reg <- reg
            op = "MOV"
        elif x_var.in_reg and not self.in_reg: # ram <- reg
            op = "STR"
        elif not x_var.in_reg and self.in_reg: # reg <- ram
            op = "LOD"
        elif not x_var.in_reg and not self.in_reg: # ram <- ram
            op = "CPY"

        urcl.append(f"{op} {x_var.pointer} {self.pointer}")

    @staticmethod
    def temp_var(type = "num", reg = False) -> str:
        name = f"TEMP_VAR_{nextvariableidentifier}"
        compiler.vars[name] = Var(name, type, type_to_width[type], reg = reg)
        return name

    def print(self):
        print(f"{self.type} variable at address {self.pointer}, with {self.width} and identifier {self.identifier}")

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

archived_handles: dict[int, bool] = {}
handle_to_reg: dict[int, str] = {} # has priority over archived_handles
handle_use = []
next_reg_handle = 0

usedregs = [0] # reg 0 doesn't count
def get_reg() -> str:
    for i in range(maxregs):
        if i not in usedregs:
            usedregs.append(i)

            return f"R{i}"
    error.error("how did we get here?")

def free_reg(reg: str):
    usedregs.remove(int(reg[1:]))

def has_free_space() -> bool:
    for i in range(config.config["regs"]):
        if i not in usedregs:
            return True
    return False

def archive_reg(handle: int, urcl: list[str]):
    global archived_handles, handle_use

    name = f"archived_{handle}"
    compiler.vars[name] = Var(name, "num", 1)
    chamber = compiler.vars[name]
    handle_use.remove(handle) # remove because archived

    # store to variable
    urcl.append(f"STR {chamber.pointer} {handle_to_reg[handle]}")
    archived_handles[handle] = True

def update_use(handle: int):
    global handle_use

    if handle_use.count(handle) == 0: # this register has never been used
        handle_use.insert(0, handle)
    else: # it already contains
        handle_use.remove(handle)
        handle_use.insert(0, handle)

def unarchive(handle: int, reg: str, urcl: list[str]) -> str:
    global handle_to_reg

    name = f'archive_{handle}'
    urcl.append(f"LOD {reg} {compiler.vars[name]}")
    handle_to_reg[handle] = reg

    return name

def handle_reg(handle: int, urcl: list[str]) -> str: # returns reg and alters urcl
    global archived_handles, handle_to_reg

    update_use(handle)

    if archived_handles[handle] == True: # register is archived
        # unarchive
        if has_free_space(): # free space to use
            reg = get_reg()

            unarchive(handle, reg, urcl)

        else: # no free space, must archive another register
            #1. archive last used register
            last_handle = handle_use[-1]
            last_reg = handle_to_reg[last_handle]
            archive_reg(last_handle, urcl)

            #2. unarchive where he was
            name = unarchive(handle, last_reg, urcl)
            compiler.vars.pop(name)

        archived_handles[handle] = False
        return reg

    else: # register is available and in register form
        return handle_to_reg[handle]

def get_reg_handle(urcl: list[str]) -> int:
    global next_reg_handle, handle_to_reg, archived_handles

    handle = next_reg_handle
    next_reg_handle += 1
    update_use(handle)

    # get a free reg
    if has_free_space():
        # free space to use
        reg = get_reg()
        handle_to_reg[handle] = reg
        archived_handles[handle] = False
    else:
        # gotta archive another reg
        last_handle = handle_use[-1]
        last_reg = handle_to_reg[last_handle]
        archive_reg(last_handle, urcl)

        handle_to_reg[handle] = last_reg
        archived_handles[handle] = False

    return handle

def free_reg_handle(handle: int):
    global handle_to_reg, archived_handles, handle_use

    if archived_handles[handle] == True:
        # if archived, remove variable
        name = f'archive_{handle}'
        compiler.vars.pop(name)
    else:
        # in reg, free reg
        reg = handle_to_reg[handle]
        free_reg(reg)

    handle_to_reg.pop(handle)
    archived_handles.pop(handle)
    handle_use.remove(handle)
