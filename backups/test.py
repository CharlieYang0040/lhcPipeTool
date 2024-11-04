def input_number(x):
    x = input(f"Enter {x} number: ")
    return x

alphaList = [chr(i) for i in range(ord('a'), ord('h'))]

for i in range(len(alphaList)):
    input_number(alphaList[i])
