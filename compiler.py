import error, config, parse
from functions import Func, Var
from shunting import shunt, to_urcl

vars: dict[str, Var] = {}
funcs: dict[str, Func] = {}
types = ["num", "array", "none"]
type_to_width = {
    "num": 1,
    "array": -1, # width is variable depending on length of array
    "none": 1
}
header = [f"BITS == {config.config['bits']}", f"MINHEAP {config.config['ram']}", f"MINREG {config.config['regs']}", f"RUN {config.config['run'].upper()}", f"MINSTACK {config.config['stack']}"]
funcrcl = []
urcl = []

def compile_expr(tokens: list[str], func = False):
    if not func:
        global urcl
    else:
        urcl = []
    
    if len(tokens) < 2:
        error.error(f"invalid syntax at {tokens}")

    if tokens[0] in types: # declaring a variable
        type = tokens[0]
        if type == "num": # declaring a number
            name = tokens[1]
            vars[name] = Var(name, type, type_to_width[type])
            if len(tokens) > 2:
                compile_expr(tokens[1:])

        elif type == "array":
            error.error("array not implemented yet")

        elif type == "none":
            name = tokens[1]
            vars[name] = Var(name, type, type_to_width[type], True)
            print("why would you even want to declare a none?")

    if tokens[1] == "=": # set
        if vars[tokens[0]].type == "num": # todo resolve functions before shunt
            urcl += to_urcl(shunt(tokens[2:], [], vars), vars, vars[tokens[0]].pointer)

    if func:
        return urcl

# compile_obj when

def add_funcrcl(urcl: list[str]):
    global funcrcl

    funcrcl += urcl

def compile_func(tokens: list[str]):
    global funcrcl

    #function add ( num x , num y ) - > num { ... }
    name = tokens[1]
    args = " ".join(tokens[tokens.index("(") + 1:tokens.index(")")]).split(",")
    args = [x.removeprefix(" ").removesuffix(" ").split(" ") for x in args]
    return_type = tokens[tokens.index(")") + 3]

    funcs[name] = Func(name, args, return_type)
    funcrcl.append(f".function_{name}")
    
    # compile insides
    parse.parse(tokens[tokens.index("{") + 1:-1], True)
