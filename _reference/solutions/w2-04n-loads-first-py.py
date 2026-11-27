def schedule(nodes):
    by_name = {n[0]: n for n in nodes}
    seen = set()
    done = []

    def needs(node):
        name, kind, version, srcs = node
        out = list(srcs)
        if kind == "store":
            out += [n[0] for n in nodes if n[1] == "load" and n[2] == version]
        return out

    def visit(name):
        if name in seen:
            return
        seen.add(name)
        for s in needs(by_name[name]):
            visit(s)
        done.append(name)

    for n in nodes:
        visit(n[0])
    return done
