from functions import Var, get_reg, free_reg
import error

# operators: + - / * % | & ^ **
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

def shunt(tokens: list[str], functions: list[str], vars: list[str]) -> list[str]: # returns in RPN
    operators: list[str] = []
    output: list[str] = []

    while len(tokens) != 0:
        token = tokens.pop(0)

        if token.isnumeric() or token in vars:
            output.append(token)

        elif token in unary_functions: # its a function
            operators.append(token)
            # TODO deal with it before so it only gives a stream of numbers and variables

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
        print("end")
        while len(operators) != 0:
            assert operators[-1] != "("

            output.append(operators.pop())

    print(output)

    return output

def handle(urcl: list[str], tempregs: list[str], x: str, vars: dict[str, Var]) -> str: # returns reg or imm
    if x.isnumeric() or x[0] == "R":
        return x
    else:
        if x not in vars:
            error.error(f"WAT, {x} is not in vars")
        else:
            tempregs.append(get_reg())
            urcl.append(f"LOD {tempregs[-1]} #{vars[x].pointer}")
            return tempregs[-1]

def trash_operand(operand):
    if operand[0] == "R": free_reg(operand)

def to_urcl(shunt: list[str], vars: dict[str, Var], pointer: int) -> list[str]:
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
                    a, b = operands[-2], operands[-1]
                    #trash_operand(operands.pop()); trash_operand(operands.pop())
                    operands.pop(); operands.pop()

                    handletemps = []
                    tempregs.append(get_reg()) 
                    result_reg = tempregs[-1]
                    urcl.append(f"{operator_to_urcl[token]} {result_reg} {handle(urcl, handletemps, a, vars)}   {handle(urcl, handletemps, b, vars)}")

                    for reg in handletemps:
                        free_reg(reg)

                    operands.append(result_reg)
                    trash_operand(a); trash_operand(b)
                else:
                    error.error("powers are unsupported for now, try later .v.")
                    
            else:
                a, b = operands[-2], operands[-1]
                operands = operands[:-2]
                exec(f"operands.append(str(int(int(a) {token} int(b))))")

    urcl.append(f"STR #{pointer} {operands[-1]}")

    for op in operands:
        if op[0] == "R":
            free_reg(op)

    return urcl
