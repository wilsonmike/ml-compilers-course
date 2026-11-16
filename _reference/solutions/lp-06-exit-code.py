import sys

def main(argv):
    if len(argv) != 2:
        print("usage: add A B", file=sys.stderr)
        return 2
    try:
        a = int(argv[0])
        b = int(argv[1])
    except ValueError:
        print("add: A and B must be whole numbers", file=sys.stderr)
        return 2
    print(a + b)
    return 0
