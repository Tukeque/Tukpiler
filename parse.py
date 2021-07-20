import compiler

def return_outsides(tokens: list[str]) -> list[str]:
    inside = False
    level = 0
    outsides: list[str] = []
    starters = ["function", "object", "for", "while", "if", "else", "elif"]

    for token in tokens:
        if inside:
            if level == 0:
                inside = False

            if token == "{":
                level += 0.5
            if token == "}":
                level -= 1

        if token in starters: # going inside
            inside = True
            level += 0.5
        
        if not inside:
            outsides.append(token)

    result = []
    for outside in outsides:
        if outside != "":
            result.append(outside)

    return result

def parse(tokens: list[str]): # returns blocks: list of tokens
    # step 1: get all the tokens that are outside functions or classes
    outsides = return_outsides(tokens)
    out_expressions = " ".join(outsides).split(";")

    new_out = []
    for out in out_expressions:
        if out != "":
            new_out.append(out)
    out_expressions: list[str] = new_out

    out_expressions = [x.removeprefix(" ").removesuffix(" ").split(" ") for x in out_expressions]
    #//out_expressions = [x.split(" ") for x in out_expressions]

    new_out = []
    for out in out_expressions:
        if out != [""]:
            new_out.append(out)
    out_expressions: list[str] = new_out
    

    # step 2: compile those
    print(out_expressions)

    for expr in out_expressions:
        compiler.compile_expr(expr)

    # step 3: call parser again with all groups of tokens going from and to curly brackets