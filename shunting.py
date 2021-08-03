import compiler, parse, functions
from functions import Var, get_reg, free_reg
import error

#* shunting yard *#
operator_list = ["+", "-", "*", "/", "%", "|", "&", "^", "**"]
operator_to_urcl = {
    "+": "ADD",
    "-": "SUB",
    "*": "MLT",
    "/": "DIV",
    "%": "MOD",
    "|": "OR" ,
    "&": "AND",
    "^": "XOR"
}
unary_functions = ["~+", "~-", "!"]

def associativity(operator) -> str:
    return {
        "+": "both",
        "-": "left",
        "/": "left",
        "*": "both",
        "%": "left",
        "|": "both",
        "&": "both",
        "^": "both",
        "~+": "right",
        "~-": "right",
        "!": "right",
        "**": "both"
    }[operator]

def precedence(operator) -> int:
    return {
        "+": 3,
        "-": 3,
        "/": 4,
        "*": 4,
        "%": 4,
        "|": 0,
        "&": 2,
        "^": 1,
        "**": 5,
        "~+": 6,
        "~-": 6,
        "!": 6
    }[operator]

#? maybe break up into smaller functions?
def shunt(tokens: list[str]) -> list[str]: # returns in RPN
    print(f"shunting {tokens}")
    operators: list[str] = []
    output: list[str] = []

    while len(tokens) != 0:
        token = tokens.pop(0)

        if token.isnumeric() or token in compiler.vars:
            output.append(token)

        elif token in unary_functions: # its a function
            operators.append(token)

        elif token in operator_list:
            while (len(operators) >= 1 and operators[-1] != "(") and (precedence(operators[-1]) > precedence(token) or (precedence(operators[-1]) == precedence(token) and associativity(token) == "left")):
                output.append(operators.pop())

            operators.append(token)

        elif token == "(":
            operators.append(token)

        elif token == ")":
            while operators[-1] != "(":
                assert len(operators) != 0 # for debug

                output.append(operators.pop())
            
            assert operators[-1] == "("
            operators.pop()

            if operators[-1] in unary_functions:
                output.append(operators.pop()) # unambiguaize
    else: # after
        while len(operators) != 0:
            assert operators[-1] != "("

            output.append(operators.pop())

    print(f"done shunting: {output}")

    return output

def handle(urcl: list[str], tempregs: list[str], x: str, vars: dict[str, Var]) -> str: # returns reg or imm
    if x.isnumeric() or x[0] == "R": return x
    else:
        if x not in vars:
            error.error(f"{x} is not in vars")
        else:
            tempregs.append(get_reg())
            urcl.append(f"LOD {tempregs[-1]} {vars[x].pointer}")
            return tempregs[-1]

def trash_operand(operand):
    if operand[0] == "R": free_reg(operand)

def handle_operator(token: str, operands: list[str], tempregs: list[str], urcl: list[str], vars):
    a, b = operands[-2], operands[-1]
    operands.pop(); operands.pop()

    handletemps = []
    tempregs.append(get_reg()) 
    result_reg = tempregs[-1]
    urcl.append(f"{operator_to_urcl[token]} {result_reg} {handle(urcl, handletemps, a, vars)} {handle(urcl, handletemps, b, vars)}")

    for reg in handletemps:
        free_reg(reg)

    operands.append(result_reg)
    trash_operand(a); trash_operand(b)

def to_urcl(shunt: list[str], vars: dict[str, Var], pointer: int, ret = False) -> list[str]:
    if shunt == []: return []
    operands = []
    tempregs = []
    urcl = []

    for token in shunt:
        if token.isnumeric() or token in vars or token[0] == "R":
            operands.append(token)
        elif token in operator_list:
            assert len(operands) >= 2

            if not(operands[-1].isnumeric() and operands[-2].isnumeric()):
                if token != "**":
                    handle_operator(token, operands, tempregs, urcl, vars)
                else:
                    error.error("powers are unsupported for now, try again later")
                    
            else:
                a, b = operands[-2], operands[-1]
                operands = operands[:-2]
                exec(f"operands.append(str(int(int(a) {token} int(b))))")

    if not ret:
        if operands[-1] in vars:
            reg = get_reg()
            urcl += [f"LOD {reg} {vars[operands[-1]].pointer}",
                     f"STR {pointer} {reg}"]
            free_reg(reg)
        else:
            urcl.append(f"STR {pointer} {operands[-1]}")
    else:
        urcl.append(f"PSH {operands[-1]}")

    for op in operands:
        if op[0] == "R":
            free_reg(op)

    return urcl

#* evaluate *#
def call_function(tokens: list[str], urcl: list[str], send_args: list[str], func_name: str, ret_var: str) -> list[str]: # returns urcl
    urcl += [f"PSH {compiler.vars[x].pointer}" for x in send_args]

    if tokens[0] in compiler.funcs and tokens.count("(") == tokens.count(")") == 1: # only a function
        name = ret_var
    else:
        name = functions.Var.temp_var()
    reg = get_reg()

    urcl += [
                f"CAL .function_{func_name}",
                f"POP {reg}",
                f"STR {compiler.vars[name].pointer} {reg}"
            ]

    free_reg(reg)
    return name

def resolve_function(tokens: list[str], i: int, urcl: list[str], ret_var: str) -> str:
    scope = parse.in_scope(tokens[i:], "(", ")")

    # loop for each arg and evaluate it to a variable
    args_split = parse.split_list(scope, ",")
    send_args = []
    temp = []

    for arg in args_split:
        assert len(arg) >= 1

        print(arg)
        if arg[0] in compiler.vars: # arg is just a variable
            send_args.append(arg[0]) # pass as reference
        else:
            name = evaluate(arg, urcl, try_reg=False)
            send_args.append(name)
            temp     .append(name)

    name = call_function(tokens, urcl, send_args, tokens[i], ret_var)
    for var in temp: compiler.vars.pop(var) # free all temp variables

    i += len(scope) + 2
    return name

def resolve(tokens: list[str], urcl: list[str], ret_var: str = "") -> list[str]: # returns a list of new shunt args with functions handled
    result = []
    i = -1
    print(f"handling {tokens}")

    while i < len(tokens) - 1:
        i += 1
        token = tokens[i]

        if token in compiler.funcs: # token is a function
            result.append(resolve_function(tokens, i, urcl, ret_var))
        else:
            result.append(token)

    print(f"resolved {result}")
    return result

def evaluate(tokens: list[str], urcl, auto_allocate = True, ret_var = "", try_reg = False, ret = False) -> str:
    """
    x - 1 --> temp_var/reg \n
    func(obj1, obj2) --> temp_var \n
    obj3 - y --> Error: not the same type
    """

    # step 1. handle functions(ok) and in-class methods/variables(todo)
    if auto_allocate:
        to_shunt = resolve(tokens, urcl)
    else:
        to_shunt = resolve(tokens, urcl, ret_var)

        if tokens[0] in compiler.funcs and tokens.count("(") == tokens.count(")") == 1: # only a function
            return ret_var

    # step 2. handle shunting yard
    rpn = shunt(to_shunt) # how to get type? # todo future get_type() function that evaluates an expression only to get the type that it returns or an exception?

    # step 3. translate RPN to urcl
    if auto_allocate:
        ret_var = Var.temp_var(reg = try_reg)
    pointer = compiler.vars[ret_var].pointer

    urcl += to_urcl(rpn, compiler.vars, pointer, ret) # todo change to_urcl to use variable and not pointer

    # step 4. profit
    return ret_var
