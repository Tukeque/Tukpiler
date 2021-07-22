import parse, lexer, error, compiler, config, sys

print("Tukeque's Programman 2021")

if len(sys.argv) == 3:
    path = sys.argv[1]
    result_name = sys.argv[2]

elif len(sys.argv) >= 2:
    print("invalid usage. usage: \".\main.py code.txt output.urcl\"")
    
else:
    path = input("file to compile: ")
    result_name = input("name of output file: ")

code = open(path, "r").readlines()

tokens = lexer.lex(code)
print(tokens)
parse.parse(tokens)

if len(error.errors) == 0:
    print(f"done! result saved in {result_name}")

    with open(result_name, "w") as f:
        f.write("\n".join(compiler.header + compiler.funcrcl + compiler.urcl))

    print(compiler.urcl)
else:
    print(f"encountered errors: \n{error.errors}")