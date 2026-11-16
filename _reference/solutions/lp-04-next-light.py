from enum import Enum

class Light(Enum):
    RED = 1
    YELLOW = 2
    GREEN = 3

NEXT = {Light.RED: Light.GREEN, Light.GREEN: Light.YELLOW, Light.YELLOW: Light.RED}

def next_light(light):
    return NEXT[light]
