from __future__ import annotations

from typing import Dict, List
import qiskit, random
from qiskit.dagcircuit.dagnode import DAGInNode, DAGOutNode, DAGOpNode
import matplotlib.pyplot as plt
import networkx as nx
import numpy as np

from qiskit_helper_functions.non_ibmq_functions import circuit_stripping
import arquin


def overlapped(node, pos):
    for other_node in pos:
        if other_node != node and np.allclose(pos[node], pos[other_node], atol=0.1, rtol=1e-1):
            return True
    return False


def find_op_node(dag, qargs):
    qubits = dag.qubits
    qubit_op_counter = [0 for _ in range(dag.num_qubits())]
    for op_node in dag.topological_op_nodes():
        if len(op_node.qargs) > 1:
            op_node_qargs = [
                (qubits.index(qarg), qubit_op_counter[qubits.index(qarg)]) for qarg in op_node.qargs
            ]
            if op_node_qargs == qargs:
                return op_node
            else:
                for qarg in op_node.qargs:
                    qubit_op_counter[qubits.index(qarg)] += 1
    return None


def draw_cut_edges(graph, pos, cut_points):
    ax = plt.gca()
    for e in graph.edges:
        cut_edge = e[:2] in cut_points
        color = "red" if cut_edge else "black"
        alpha = 0.9
        delta_x, delta_y = pos[e[1]] - pos[e[0]]
        xy = (pos[e[1]][0] - (1 + alpha) / 2 * delta_x, pos[e[1]][1] - (1 + alpha) / 2 * delta_y)
        xytext = (
            pos[e[1]][0] - (1 - alpha) / 2 * delta_x,
            pos[e[1]][1] - (1 - alpha) / 2 * delta_y,
        )
        ax.annotate(
            "",
            xy=xy,
            xycoords="data",
            xytext=xytext,
            textcoords="data",
            arrowprops=dict(
                arrowstyle="<-",
                color=color,
                shrinkA=5,
                shrinkB=5,
                patchA=None,
                patchB=None,
                connectionstyle="arc3,rad=rrr".replace("rrr", str(0.3 * e[2])),
            ),
        )


def get_node_pos(graph, layout_name):
    layout_method = getattr(nx, layout_name)
    pos = layout_method(graph)
    node_pos = {}
    for node in pos:
        node_pos[node] = pos[node]
        while overlapped(node, node_pos):
            node_pos[node] += [random.uniform(-0.5, 0.5) for _ in range(2)]
    return node_pos


def get_node_labels(graph, qubits):
    op_node_counter = 0
    node_labels = {}
    for node in graph.nodes:
        if type(node) is DAGInNode:
            node_labels[node] = "q%d" % qubits.index(node.wire)
        elif type(node) is DAGOutNode:
            node_labels[node] = "q%d" % qubits.index(node.wire)
        elif type(node) is DAGOpNode:
            node_labels[node] = "%s%d" % (node.op.name, op_node_counter)
            op_node_counter += 1
    return node_labels


def get_node_colors(graph, qubits):
    node_colors = []
    for node in graph.nodes:
        if type(node) is DAGInNode:
            node_colors.append("lime")
        elif type(node) is DAGOutNode:
            node_colors.append("red")
        elif type(node) is DAGOpNode:
            node_colors.append("royalblue")
    return node_colors


def plot_recursion(
    recursion_counter: int,
    device: arquin.device.Device,
    remaining_virtual_circuit: qiskit.QuantumCircuit,
    distribution: List,
    output_circuit: qiskit.QuantumCircuit,
) -> None:

    # stripped_remaining_virtual = circuit_stripping(remaining_virtual_circuit)
    # remaining_virtual_dag = qiskit.converters.circuit_to_dag(stripped_remaining_virtual)
    # remaining_virtual_graph = remaining_virtual_dag.to_networkx()
    # node_pos = get_node_pos(remaining_virtual_graph, layout_name='planar_layout')
    # node_labels = get_node_labels(remaining_virtual_graph, qubits=remaining_virtual_circuit.qubits)
    # node_colors = get_node_colors(remaining_virtual_graph, qubits=remaining_virtual_circuit.qubits)
    # nx.draw_networkx_nodes(remaining_virtual_graph, node_color=node_colors, pos=node_pos, node_shape='o', node_size=700)
    # nx.draw_networkx_labels(remaining_virtual_graph, labels=node_labels, pos=node_pos)
    # draw_cut_edges(graph=remaining_virtual_graph, pos=node_pos, cut_points=[])
    # plt.axis("off")
    # plt.savefig("./workspace/remaining_virtual_circuit_%d.pdf" % recursion_counter, format='pdf')
    # plt.close()

    remaining_virtual_circuit.draw(
        output="mpl",
        fold=500,
        filename="./workspace/remaining_virtual_circuit_%d.pdf" % recursion_counter,
    )
    plt.close()

    # remaining_virtual_dag = qiskit.converters.circuit_to_dag(remaining_virtual_circuit)
    # remaining_virtual_dag.draw(
    #     filename="./workspace/remaining_virtual_dag_%d.pdf" % recursion_counter, style="color"
    # )
    # plt.close()

    for module in device.modules:
        module.virtual_circuit.draw(
            output="mpl",
            fold=500,
            filename="./workspace/module_%d_virtual_%d.pdf"
            % (module.module_index, recursion_counter),
        )
        module.physical_circuit.draw(
            output="mpl",
            fold=500,
            filename="./workspace/module_%d_physical_%d.pdf"
            % (module.module_index, recursion_counter),
        )
    output_circuit.draw(
        output="mpl", fold=500, filename="./workspace/output_%d.pdf" % recursion_counter
    )
