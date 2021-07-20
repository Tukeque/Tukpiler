import error, config
from functions import Var
from shunting import shunt, to_urcl

vars: dict[str, Var] = {}
types = ["num", "array", "none"]
type_to_width = {
    "num": 1,
    "array": -1, # width is variable depending on length of array
    "none": 1
}
urcl = [f"BITS == {config.config['bits']}", f"MINHEAP {config.config['ram']}", f"MINREG {config.config['regs']}", f"RUN {config.config['run'].upper()}", f"MINSTACK {config.config['stack']}"]

def compile_expr(tokens: list[str]):
    global urcl
    
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
