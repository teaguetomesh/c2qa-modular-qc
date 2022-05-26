import subprocess
from typing import Dict, Iterable, List, Tuple

import networkx as nx
import qiskit


def edges_to_source_graph(edges, vertex_weights: Dict) -> Dict:
    """Convert given graph to SCOTCH format"""
    adjacency = {}
    for edge in edges:
        for counter in range(2):
            vertex = edge[counter]
            other_vertex = edge[(counter + 1) % 2]
            if vertex in adjacency:
                if other_vertex in adjacency[vertex]:
                    adjacency[vertex][other_vertex] += 1
                else:
                    adjacency[vertex][other_vertex] = 1
            else:
                adjacency[vertex] = {other_vertex: 1}
    n_vertices = len(adjacency)
    n_edges = len(edges)

    has_vertex_weights = vertex_weights is not None
    has_edge_weights = True
    has_vertex_labels = False
    source_graph = {
        0: "0\n",
        1: "%d %d\n" % (n_vertices, 2 * n_edges),
        2: "0 %d%d%d\n" % (has_vertex_labels, has_edge_weights, has_vertex_weights),
    }
    for vertex_idx in adjacency:
        line_num = vertex_idx + 3
        line = ""
        if has_vertex_weights:
            line += "%d " % vertex_weights[vertex_idx]
        line += "%d " % len(adjacency[vertex_idx])
        for neighbor in adjacency[vertex_idx]:
            load = adjacency[vertex_idx][neighbor]
            line += "%d %d " % (load, neighbor)
        line += "\n"
        source_graph[line_num] = line
    return source_graph


def circuit_to_graph(circuit):
    dag = qiskit.converters.circuit_to_dag(circuit)
    vertex_weights = []
    id_to_idx = {}  # Gate id to gate idx
    idx_to_gate = []  # Gates in topological order
    dirty_qubits = []
    for vertex in dag.topological_op_nodes():
        id_to_idx[id(vertex)] = len(idx_to_gate)
        idx_to_gate.append(vertex)
        vertex_weight = 0
        for qarg in vertex.qargs:
            if qarg not in dirty_qubits:
                dirty_qubits.append(qarg)
                vertex_weight += 1
        vertex_weights.append(vertex_weight)

    edges = []
    for u, v, _ in dag.edges():
        if u.type == "op" and v.type == "op":
            u_idx = id_to_idx[id(u)]
            v_idx = id_to_idx[id(v)]
            edges.append((u_idx, v_idx))

    return vertex_weights, edges


def write_source_graph_file(graph, save_dir, fname):
    graph_file = open("%s/%s_source.txt" % (save_dir, fname), "w")
    for line_num in range(len(graph)):
        graph_file.write(graph[line_num])
    graph_file.close()
    # subprocess.call(["/home/weit/scotch/build/bin/gtst", "%s/%s_source.txt" % (save_dir, fname)])


def write_target_graph_file(graph, save_dir, fname):
    write_source_graph_file(graph=graph, save_dir=save_dir, fname=fname)
    subprocess.call(
        [
            "/home/weit/scotch/build/bin/amk_grf",
            "%s/%s_source.txt" % (save_dir, fname),
            "%s/%s_target.txt" % (save_dir, fname),
        ]
    )
    subprocess.call(["rm", "%s/%s_source.txt" % (save_dir, fname)])


def edges_to_coupling_map(edges):
    coupling_map = []
    for edge in edges:
        assert len(edge) == 2 and edge[0] != edge[1]
        coupling_map.append(list(edge))
        coupling_map.append(list(edge[::-1]))
    return coupling_map

def reverse_dict(dictionary: Dict) -> Dict:
    reverse_dict = {}
    for key in dictionary:
        reverse_dict[dictionary[key]] = key
    return reverse_dict