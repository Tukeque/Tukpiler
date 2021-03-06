import compiler, parse, functions, config
from functions import Var, archive_reg, get_reg, free_reg, get_reg_from_handle, get_reg_handle, free_reg_handle, handle_reg
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

class Token:
    def __init__(self, content: str, type: str):
        self.content = content
        self.type = type

def get_type_from_token(token: str) -> str:
    if token in operator_list + unary_functions:
        return "operator"
    elif token.isnumeric() or token in compiler.vars:
        return "operand"

def shunt(tokens: list[str]) -> list[Token]: # returns in RPN
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

    objectoutput = []
    for out in output:
        objectoutput.append(Token(out, get_type_from_token(out)))

    return objectoutput

class Operand:
    def __init__(self, content: str, type: str):
        self.content = content
        self.type = type

    def get(self, urcl: list[str], temp_handles: list[int] = []) -> str: # returns reg
        if self.type == "imm":
            return self.content

        elif self.type == "handle":
            reg = handle_reg(int(self.content), urcl)
            temp_handles.append(int(self.content))
            return reg

        elif self.type == "var":
            reg_handle = compiler.vars[self.content].get(urcl)
            if not compiler.vars[self.content].in_reg:
                temp_handles.append(reg_handle)
            return handle_reg(reg_handle, urcl)

    def push(self, urcl: list[str]):
        if config.config["complex"] == True:
            if self.type == "imm": # make var
                name = Var.temp_var()
                compiler.vars[name].set(self.content, urcl)
                urcl.append(f"PSH {compiler.vars[name].pointer}")

            elif self.type == "var": # easy
                if not compiler.vars[self.content].in_reg: # in memory
                    urcl.append(f"PSH {compiler.vars[self.content].pointer}")
                else: # in reg
                    handle = compiler.vars[self.content].handle
                    archive_reg(handle, urcl)
                    urcl.append(f"PSH {compiler.vars[f'archived_{handle}'].pointer}")

            elif self.type == "handle":
                handle = int(self.content)
                archive_reg(handle, urcl)
                urcl.append(f"PSH {compiler.vars[f'archived_{handle}'].pointer}")
        else:
            if self.type == "imm":
                urcl.append(f"PSH {self.content}")

            elif self.type == "var":
                urcl.append(f"PSH {compiler.vars[self.content].get(urcl)}")

            elif self.type == "handle":
                urcl.append(f"PSH {handle_reg(int(self.content), urcl)}")

def trash_operand(operand: Operand):
    if operand.type == "handle":
        free_reg_handle(int(operand.content))

def handle_operator(token: Token, operands: list[Operand], temp_handles: list[int], urcl: list[str]):
    b = operands.pop()
    a = operands.pop()

    operand_temps = []
    result_handle = get_reg_handle(urcl)
    temp_handles.append(result_handle)

    for x in [a, b]:
        if x.content.isnumeric():
            if int(x.content) in temp_handles: # was a temp_handle before
                temp_handles.remove(int(x.content))

    urcl.append(f"{operator_to_urcl[token.content]} {handle_reg(result_handle, urcl)} {a.get(urcl, operand_temps)} {b.get(urcl, operand_temps)}")

    for handle in operand_temps:
        free_reg_handle(handle)

    operands.append(Operand(str(result_handle), "handle"))
    #trash_operand(a); trash_operand(b)

def to_urcl(rpn: list[Token], ret_var: str, ret = False) -> list[str]:
    if rpn == []: return []
    operands: list[Operand] = []
    temp_handles = []
    urcl = []

    for token in rpn:
        if token.type == "operand":
            if token.content.isnumeric():
                operands.append(Operand(token.content, "imm"))
            else:
                assert token.content in compiler.vars
                operands.append(Operand(token.content, "var"))

        elif token.type == "operator":
            assert len(operands) >= 2

            if not(operands[-1].type == operands[-2].type == "imm"):
                if token != "**":
                    handle_operator(token, operands, temp_handles, urcl)
                else:
                    error.error("powers are unsupported for now, try again later")
                    
            else:
                b = operands.pop().content
                a = operands.pop().content
                exec(f"operands.append(Operand(str(int(a {token.content} b)), 'imm'))")

    assert len(operands) == 1

    if not ret:
        value = operands[-1].content
        if operands[-1].type == "handle":
            value = int(value)
        
        compiler.vars[ret_var].set(value, urcl)
    else:
        operands[-1].push(urcl)

    for handle in temp_handles:
        free_reg_handle(handle)

    return urcl

#* evaluate *#
def call_function(tokens: list[str], urcl: list[str], send_args: list[str], func_name: str, ret_var: str) -> list[str]: # returns urcl
    urcl += [f"PSH {compiler.vars[x].get_pointer(urcl)}" for x in send_args]

    if tokens[0] in compiler.funcs and tokens.count("(") == tokens.count(")") == 1: # only a function
        name = ret_var
    else:
        name = functions.Var.temp_var()

    if config.config["complex"] == True:
        reg_handle = get_reg_handle(urcl)
        urcl += [
                    f"CAL .function_{func_name}",
                    f"POP {handle_reg(reg_handle, urcl)}",
                ]
        # handle_reg is pointer
        
        if not compiler.vars[name].in_reg:
            urcl.append(f"CPY {compiler.vars[name].pointer} {get_reg_from_handle(reg_handle)}")
            print("copy!")
        else:
            urcl.append(f"LOD {handle_reg(compiler.vars[name].handle, urcl)} {get_reg_from_handle(reg_handle)}")
    else:
        reg_handle = get_reg_handle(urcl)
        urcl += [
                    f"CAL .function_{func_name}",
                    f"POP {handle_reg(reg_handle, urcl)}",
                ]
        compiler.vars[name].set(reg_handle, urcl)

        free_reg_handle(reg_handle)

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
        if len(arg) == 1 and arg[0] in compiler.vars: # arg is just a variable
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
    if len(tokens) == 1 and tokens[0] in compiler.vars:
        if ret:
            reg_handle = compiler.vars[tokens[0]].get(urcl)
            urcl.append(f"PSH {handle_reg(reg_handle, urcl)}")
            if not compiler.vars[tokens[0]].in_reg:
                free_reg_handle(reg_handle)
            return tokens[0]
        else:
            return tokens[0]
    if tokens == []:
        name = f"NULL_{functions.nextvariableidentifier}"
        compiler.vars[name] = Var(name, "none", 1, at_zero=True)
        return name

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
    if auto_allocate and not ret:
        ret_var = Var.temp_var(reg = try_reg)

    urcl += to_urcl(rpn, ret_var, ret)

    # step 4. profit
    return ret_var
