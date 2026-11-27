def shrink_offsets(pads):
    return pads[0::2]


def pad_widths(offsets, sizes, dims):
    out = []
    for o, s, d in zip(offsets, sizes, dims):
        out += [o, d - o - s]
    return out
