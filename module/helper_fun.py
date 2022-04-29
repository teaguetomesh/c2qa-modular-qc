def add_flip_edges(edges):
    ret = []
    for edge in edges:
        ret.append(edge)
        ret.append(edge[::-1])
    return ret