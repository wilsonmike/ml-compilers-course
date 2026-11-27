def good_count(text):
    return len(text.split())

def bad_count(text):
    return len(text.split(" "))

CASES = [("the cat sat", 3), ("", 0), ("one", 1), ("  two   words ", 2)]

def failures(f, cases):
    failed = 0
    for given, expected in cases:
        got = f(given)
        if got != expected:
            failed += 1
    return failed
