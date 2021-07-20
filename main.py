from functions import Var
from shunting import shunt, to_urcl
import parse, lexer, error, compiler, config

print("Tukeque's Programman 2021")

path = input("file to compile: ")
result_name = input("name of output file: ")

code = open(path, "r").readlines()

tokens = lexer.lex(code)
print(tokens)
parse.parse(tokens)

#//print(shunt("3 + ~- 4".split(" "), [], ["x", "y", "z"]))
#//compiler.vars["x"] = Var("x", "num", 1)
#//compiler.vars["y"] = Var("y", "num", 1)
#//compiler.vars["z"] = Var("z", "num", 1)
#//print(to_urcl(shunt(["x", "+", "y", "*", "(", "8", "/", "3", "+", "z", ")", "+", "67"], [], ["x", "y", "z"]), compiler.vars, 10))

if len(error.errors) == 0:
    print(f"done! result saved in {result_name}")

    with open(result_name, "w") as f:
        if config.config["modfix"] == True:
            f.write("\n".join(compiler.urcl).replace("#", "M"))
        else:
            f.write("\n".join(compiler.urcl))

    print(compiler.urcl)
else:
    print(f"encountered errors: \n{error.errors}")