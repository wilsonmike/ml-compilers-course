def create():
    table = {}
    def make(name):
        if name not in table:
            table[name] = len(table)
        return table[name]
    return make
