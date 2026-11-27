def run(lines: list[list]) -> dict[str, int]:
    env = {"start": 0}
    for line in lines:
        name = line[0]
        earlier = line[1]
        n = line[2]
        value = env[earlier] + n
        env[name] = value
    return env
