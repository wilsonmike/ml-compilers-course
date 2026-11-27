def run(schedule: list[int]) -> int:
    counter = 0
    reg = [0, 0]
    step = [0, 0]
    for t in schedule:
        if step[t] % 3 == 0:
            reg[t] = counter
        elif step[t] % 3 == 1:
            reg[t] = reg[t] + 1
        else:
            counter = reg[t]
        step[t] += 1
    return counter
