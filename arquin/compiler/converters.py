import subprocess
from typing import Dict, Iterable, List, Tuple

import networkx as nx
import qiskit


def edges_to_source_graph(graph: nx.Graph) -> Dict:
    """Convert given graph to SCOTCH format"""
    adjacency: Dict = {vertex_idx: {} for vertex_idx in range(n_vertices)}
    distinct_edges = set()
    for edge in edges:
        u, v = edge
        distinct_edges.add(tuple(sorted(edge)))
        if v not in adjacency[u]:
            adjacency[u][v] = 1
        else:
            adjacency[u][v] += 1
        if u not in adjacency[v]:
            adjacency[v][u] = 1
        else:
            adjacency[v][u] += 1

    vertex_weights = False
    edge_weights = True
    vertex_labels = False
    source_graph = {
        0: "0\n",
        1: "%d %d\n" % (n_vertices, 2 * len(distinct_edges)),
        2: "0 %d%d%d\n" % (vertex_labels, edge_weights, vertex_weights),
    }
    for vertex_idx in adjacency:
        line_num = vertex_idx + 3
        line = "%d " % len(adjacency[vertex_idx])
        for neighbor in adjacency[vertex_idx]:
            load = adjacency[vertex_idx][neighbor]
            line += "%d %d " % (load, neighbor)
        line += "\n"
        source_graph[line_num] = line
    return source_graph


def circuit_to_edges(circuit: qiskit.QuantumCircuit) -> Tuple:
    dag = qiskit.converters.circuit_to_dag(circuit)
    edges = []
    node_name_ids = {}
    id_node_names = {}
    vertex_ids = {}
    curr_node_id = 0
    qubit_gate_counter = {}
    for qubit in dag.qubits:
        qubit_gate_counter[qubit] = 0
    for vertex in dag.topological_op_nodes():
        if len(vertex.qargs) != 2:
            raise Exception("vertex does not have 2 qargs!")
        arg0, arg1 = vertex.qargs
        vertex_name = "%s[%d]%d %s[%d]%d" % (
            arg0.register.name,
            arg0.index,
            qubit_gate_counter[arg0],
            arg1.register.name,
            arg1.index,
            qubit_gate_counter[arg1],
        )
        qubit_gate_counter[arg0] += 1
        qubit_gate_counter[arg1] += 1
        # print(vertex.op.label,vertex_name,curr_node_id)
        if vertex_name not in node_name_ids and id(vertex) not in vertex_ids:
            node_name_ids[vertex_name] = curr_node_id
            id_node_names[curr_node_id] = vertex_name
            vertex_ids[id(vertex)] = curr_node_id
            curr_node_id += 1

    for u, v, _ in dag.edges():
        if u.type == "op" and v.type == "op":
            u_id = vertex_ids[id(u)]
            v_id = vertex_ids[id(v)]
            edges.append((u_id, v_id))

    n_vertices = dag.size()
    return n_vertices, edges, node_name_ids, id_node_names


def write_source_graph_file(graph: Dict, fname: str) -> None:
    graph_file = open("workspace/%s_source.txt" % fname, "w")
    for line_num in range(len(graph)):
        graph_file.write(graph[line_num])
    graph_file.close()
    # subprocess.call(['/home/weit/scotch/build/bin/gtst','workspace/%s_source.txt'%fname])


def write_target_graph_file(graph: Dict, fname: str) -> None:
    write_source_graph_file(graph=graph, fname=fname)
    subprocess.call(
        [
            "/home/weit/scotch/build/bin/amk_grf",
            "workspace/%s_source.txt" % fname,
            "workspace/%s_target.txt" % fname,
        ]
    )
    subprocess.call(["rm", "workspace/%s_source.txt" % fname])
