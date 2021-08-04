import error, config, parse, functions
from functions import Func, Var, free_reg, get_reg
from shunting import shunt, to_urcl, evaluate
from copy import copy

vars: dict[str, Var] = {}
funcs: dict[str, Func] = {}
header = [f"BITS == {config.config['bits']}", f"MINHEAP {config.config['ram']}", f"MINREG {config.config['regs']}", f"RUN {config.config['run'].upper()}", f"MINSTACK {config.config['stack']}", "JMP .main"]
funcrcl = []
func_name = ""
func_ret_addr = ""
urcl = [".main"]

cond_identifier = 0
cond_to_urcl_inverse = {
    ">=": "BRL", # BGE
    "<=": "BRG", # BLE
    ">": "BLE", # BRG
    "<": "BGE", # BRL
    "==": "BNE", # BEQ
    "!=": "BRE" # BNQ
}

def add_urcl(content: list[str]):
    global urcl
    urcl += content

def add_funcrcl(urcl: list[str]):
    global funcrcl
    funcrcl += urcl

def declare(tokens: list[str], urcl: list[str]):
    global vars

    type = tokens[0]
    if type == "num": # declaring a number
        name = tokens[1]
        vars[name] = Var(name, type, functions.type_to_width[type])
        if len(tokens) > 2:
            compile_expr(tokens[1:], urcl)

    elif type == "array":
        error.error("array not implemented yet")

    elif type == "none":
        name = tokens[1]
        vars[name] = Var(name, type, functions.type_to_width[type], True)
        print("why would you even want to declare a none?")

def compile_expr(tokens: list[str], urcl: list[str]):
    print(f"compiling expression {tokens}")
    
    if len(tokens) < 2:
        error.error(f"invalid syntax at {tokens}")

    if tokens[0] in functions.types: # declaring a variable
        declare(tokens, urcl)

    if tokens[1] == "=": # set
        evaluate(tokens[2:], urcl, auto_allocate=False, ret_var=tokens[0])

    if tokens[0] == "return": # returning
        if funcs[func_name].return_type == "num":
            urcl += to_urcl(shunt(tokens[1:]), "", ret = True)
            urcl += [f"PSH {func_ret_addr}", "RET"]

def compile_func(tokens: list[str]): # maybe clean up
    global funcrcl, func_name, func_ret_addr, vars
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

    # return adress stack fix
    return_address = get_reg()
    funcrcl.append(f"POP {return_address}")
    func_ret_addr = return_address

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
        funcrcl += ["PSH R0", f"PSH {func_ret_addr}", "RET"] # R0 = none

    # free & clean up
    for arg in arg_table: free_reg(arg_table[arg])
    vars = before
    free_reg(return_address)

def find_comparator(tokens: list[str]):
    comparators = [">=", "<=", "==", "!=", ">", "<"]
    comp_count = 0
    i = -1

    for comparator in comparators:
        if tokens.count(comparator) >= 1:
            comp_count += tokens.count(comparator)

            i = tokens.index(comparator)

    if comp_count == 0: error.error("no comparator found in conditional statement")
    if comp_count > 1: error.error("too many comparators in conditional statement(will be fixed later)") # todo fix later
    if comp_count == 1:
        return i

def compile_cond(tokens: list[str], urcl: list[str], func: False):
    global cond_identifier
    print(f"condition {tokens}")
    
    # step 1. evaluate condition
    end = tokens.index("{")
    comp_index = find_comparator(tokens[:end])

    comparator = tokens[comp_index]
    a = evaluate(tokens[1:comp_index], urcl)
    b = evaluate(tokens[comp_index + 1:end], urcl)

    if vars[a].type == vars[b].type:
        type = vars[a].type

        if type == "num":
            urcl.append(f"{cond_to_urcl_inverse[comparator]} .end_{cond_identifier} {vars[a].get(urcl)} {vars[b].get(urcl)}")

        elif type == "none":
            error.error("why are you trying to compare nones") #wtf am i suposed to do? compare nulls?

        else: # class
            if comparator in [">=", "<=", ">", "<"]:
                error.error("cant compare classes with numerical comparations")    
            else:
                error.error("class comparison not implemented yet") # TODO
    else:
        error.error("trying to compare two variables with different types")

    # step 2. compile outcomes
    incremented = False
    if_scope = tokens[tokens.index("{") + 1:tokens.index("}")]
    parse.parse(if_scope, func)
    urcl.append(f".end_{cond_identifier}")

    if len(tokens) > len(tokens[:tokens.index("{") + 1]) + len(if_scope) + 1: # theres more
        if tokens[tokens.index("}") + 1] == "else":
            else_scope = tokens[tokens.index("}") + 3:-1]
            parse.parse(else_scope, func)
        elif tokens[tokens.index("}") + 1] == "elif":
            rest_scope = tokens[tokens.index("}") + 1:]
            rest_scope[0] = "if"

            cond_identifier += 1
            incremented = True
            compile_cond(rest_scope, urcl, func)

    if not incremented:
        cond_identifier += 1

# compile_obj when
