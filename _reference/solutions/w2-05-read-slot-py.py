import struct


def read_slot(out: str, k: int) -> list[float]:
    vals = []
    for line in out.splitlines():  # handles \n and \r\n
        parts = line.split()  # [] for a blank line
        if len(parts) == 2 and int(parts[0]) == k:
            vals.append(struct.unpack(">f", bytes.fromhex(parts[1]))[0])
    return vals
