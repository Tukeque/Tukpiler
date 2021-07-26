import error, config, parse, functions
from functions import Func, Var, free_reg, get_reg
from shunting import shunt, to_urcl
from copy import copy

vars: dict[str, Var] = {}
funcs: dict[str, Func] = {}
types = ["num", "array", "none"]
type_to_width = {
    "num": 1,
    "array": -1, # width is variable depending on length of array
    "none": 1
}
header = [f"BITS == {config.config['bits']}", f"MINHEAP {config.config['ram']}", f"MINREG {config.config['regs']}", f"RUN {config.config['run'].upper()}", f"MINSTACK {config.config['stack']}", "JMP .main"]
funcrcl = []
func_name = ""
urcl = [".main"]

def add_urcl(content: list[str]):
    global urcl

    urcl += content

# TODO clean vvv
def resolve(tokens: list[str]) -> list[str]:
    urcl = []

    if vars[tokens[0]].type == "num":
        to_shunt = []
        i = -1
        print(f"resolving {tokens[2:]}")
        while i < len(tokens[2:]) - 1:
            i += 1
            token = tokens[2:][i]

            if token in funcs: # token is a function (power( ... ))
                scope = parse.in_scope(tokens[2:][i:], "(", ")")

                # loop for each arg and shunt it to a variable
                args_split = [x.removeprefix(" ").removesuffix(" ").split(" ") for x in " ".join(scope).split(",")]
                send_args: list[str] = []
                temp: list[str] = []

                for arg in args_split:
                    assert len(arg) >= 1

                    if len(arg) == 1 and arg[0] in vars: # arg is just a variable
                        send_args.append(arg[0])
                    else:
                        name = f"TEMP_VAR_{functions.nextvariableidentifier}" # how to get type? # todo future get_type() function that evaluates an expression only to get the type that it returns or an exception?
                        vars[name] = Var(name, "num", 1) #! ^
                        send_args.append(name)
                        temp.append(name)

                        urcl += resolve([name, "="] + arg)

                urcl += [f"PSH {vars[x].pointer}" for x in send_args]

                name = f"TEMP_VAR_{functions.nextvariableidentifier}"
                vars[name] = Var(name, "num", 1)
                reg = get_reg()

                urcl += [f"CAL .function_{token}",
                         f"POP {reg}",
                         f"STR {vars[name].pointer} {reg}"]

                to_shunt.append(name)
                free_reg(reg)

                for var in temp:
                    vars.pop(var)

                i += len(scope) + 2
            else:
                to_shunt.append(token)

        print(f"resolved {to_shunt}")

        urcl += to_urcl(shunt(to_shunt, vars), vars, vars[tokens[0]].pointer)

    return urcl

def declare(tokens: list[str]):
    global vars

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

def compile_expr(tokens: list[str], func = False):
    print(f"compiling expression {tokens}")
    urcl = []
    
    if len(tokens) < 2:
        error.error(f"invalid syntax at {tokens}")

    if tokens[0] in types: # declaring a variable
        declare(tokens)

    if tokens[1] == "=": # set
        urcl += resolve(tokens)

    if tokens[0] == "return": # returning
        if funcs[func_name].return_type == "num":
            urcl += to_urcl(shunt(tokens[1:], vars), vars, 0, ret = True)
            urcl.append("RET")

    if not func: add_urcl(urcl)

    return urcl

def add_funcrcl(urcl: list[str]):
    global funcrcl
    funcrcl += urcl

def compile_func(tokens: list[str]):
    global funcrcl, func_name, vars
    print(f"compiling function {tokens}")
    #function add ( num x , num y ) - > num { ... }

    name = tokens[1]
    func_name = name
    args = parse.split_list(tokens[tokens.index("(") + 1:tokens.index(")")], ",")
    print(args)
    return_type = tokens[tokens.index(")") + 3]

    funcs[name] = Func(name, args, return_type)
    funcrcl.append(f".function_{name}")
    arg_table: dict[str, str] = {}

    # extract arguments' pointers and create/overwrite the variables
    before = copy(vars)
    for arg in args:
        reg = get_reg()
        arg_table[arg[1]] = reg # setup an argument to reg table
        funcrcl.append(f"POP {reg}")
        vars[arg[1]] = Var(arg[1], arg[0], 1, argument = True, reg = reg)    
    
    # compile insides
    parse.parse(tokens[tokens.index("{") + 1:-1], True)

    if funcrcl[-1][0:3] != "RET": # add return if it doesnt have one
        funcrcl += ["PSH 0", "RET"]

    # return
    for arg in arg_table: free_reg(arg_table[arg])
    vars = before

# compile_obj when
