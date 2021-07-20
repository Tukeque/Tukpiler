import error

def preprocess(code: list[str]) -> list[str]:
    for i, line in enumerate(code):
        code[i] = line.replace("\n", "")

        if line.count("//") >= 1:
            code[i] = line[:line.index("//")] # remove comments

        if line.count("#") >= 1:
            code[i] = line[:line.index("#")] # remove comments

    return code

def lex(code: list[str]) -> list[str]:
    code = preprocess(code)
    stream = ";".join(code)
    tokens: list[str] = []
    token = ""

    # lexer args
    lexing_tokens = ["+", "//", "*", "^", "&", "|", "-", "num", "function", "object", "=", "==", ">=", "<=", "!=", ">", "<", "none", "array", "->", "{", "}", "\"", "[", "]", ",", "(", ")", "$", ".", ";", "%"]
    separators = [" "]

    for i in range(len(stream)): # TODO string check (use a function to generate an array of bools to get if a certain char is in string(doesnt matter and is the same token) or if its not and should be counted)
        char = stream[i]

        if char in separators:
            if token.replace(" ", "").replace(";", "") != "":
                tokens.append(token)
                token = ""
        else:
            if char in lexing_tokens:
                if token.replace(" ", "").replace(";", "") != "":
                    tokens.append(token)
                    token = ""
                tokens.append(char)
            else:
                token += char
            
                if token in lexing_tokens: # token is fully found
                    tokens.append(token)
                    token = ""

    if token.replace(" ", "").replace(";", "") != "":
        tokens.append(token)
        token = ""

    operators = ["+", "-", "*", "/", "%", "|", "&", "^", "=", "("]
    for i in range(len(tokens)):
        token = tokens[i]

        if token == "+" or token == "-":
            if tokens[-1] in operators: # its unary
                tokens[i] = f"~{token}"
                print("unarized!")

    return tokens