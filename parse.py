import error, compiler, functions

def split_list(ls: list[str], splitter: str) -> list[list[str]]:
    result = " ".join(ls).split(splitter)
    result = [x.removeprefix(" ").removesuffix(" ").split(" ") for x in result] # num x
    return result

def in_scope(tokens: list[str], enter: str, exit: str) -> list[str]:
    level = 0
    inside = False
    result = []

    for token in tokens:
        if inside:
            if token == exit:
                level -= 1

            if level == 0:
                return result

            elif token == enter:
                level += 1

        if inside:
            result.append(token)

        if token == enter:
            level += 1
            inside = True

    return result

def is_expr(expr: list[str]):
    if expr[1] == "=" or expr[0] in functions.types or expr[0] == "return":
        return True
    return False

def parse(tokens: list[str], func = False): # new parse
    expr = []
    print(f"tokens to parse {tokens}")
    tokens += ";"

    i = -1
    while i < len(tokens) - 1:
        i += 1
        token = tokens[i]

        if token == ";":
            if expr != [] and len(expr) >= 2:
                if expr[0] == "function":
                    f = tokens[i-len(expr):]
                    f = f[:f.index("{") + 1] + in_scope(f, "{", "}")  + ["}"]

                    compiler.compile_func(f)
                    i += len(in_scope(tokens[i-len(expr):], "{", "}"))

                elif expr[0] == "object":
                    error.error("objects arent implemented yet. try again later")

                elif expr[0] == "if":
                    block = expr + in_scope(tokens[i-len(expr):], "{", "}")  + ["}"]
                    i += len(in_scope(tokens[i-len(expr):], "{", "}"))

                    while True: # check for else or elif
                        rest = tokens[i + 1:]
                        if rest[0] == "else" or rest[0] == "elif":
                            mini_block = rest[:rest.index("{")] + in_scope(rest, "{", "}") + ["}"]
                            block += mini_block

                            i += len(mini_block)
                        else:
                            break

                    compiler.compile_cond(block, compiler.funcrcl if func else compiler.urcl, func)

                elif is_expr(expr):
                    compiler.compile_expr(expr, compiler.funcrcl if func else compiler.urcl)

            expr = []
        else:
            expr.append(token)
