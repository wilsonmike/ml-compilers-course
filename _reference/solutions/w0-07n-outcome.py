class Rejected(Exception):
    pass


def check(text: str) -> None:
    for line in text.splitlines():
        if not line.startswith("%"):
            raise Rejected("bad line")


def judge(path: str, text: str) -> str:
    try:
        check(text)
    except Rejected:
        return "REJECTED " + path
    return "MATCH " + path
