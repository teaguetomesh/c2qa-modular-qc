from __future__ import annotations

from typing import Dict, List

import networkx as nx
import numpy as np

import arquin


class Device:
    """Class representing a single quantum computer.

    Provides the properties ``graph``, ``modules``, ``global_edges``, ``local_edges``, and ``size``.

    DEFINE THE DIFFERENT GRAPHS AND QUBIT REPRESENTATIONS HERE
    The nodes of the device graph represent individual modules.
    """

    def __init__(self, global_edges: List[List[List[int]]], module_graphs: List[nx.Graph]) -> None:
        """Construct a new Device object

        Input
        -----
        global_edges: Nested list indicating the connectivity between modules. An edge between two
            qubits, `qubit_i_j` and `qubit_k_l`, residing in separate modules, is called a
            'global edge'. It is represented represented as [[i, j], [k, l]], where `i` and `k`
            are the indices of the two modules and `j` and `l` are the local physical qubit indices
            with respect to each module.
        module_graphs: list of graphs of each module
        """
        self.global_edges = global_edges  # qubits are in module format

        # Nodes are modules, edges are (module_i, module_j)
        self.graph = self._build_device_graph()

        assert len(module_graphs) == self.graph.size()

        self.modules, self.d2m_p2p_mapping, self.m2d_p2p_mapping = self._build_modules(module_graphs)

        # Nodes are device qubits, edges are (qubit_i, qubit_j)
        self.physical_qubit_graph = self._construct_qubit_graph()

        self.size = sum([module.size for module in self.modules])

    def _build_device_graph(self) -> nx.Graph:
        """Construct the device graph using the global edges."""
        device_graph = nx.Graph()
        intermodule_edges = [[edge[0][0], edge[1][0]] for edge in self.global_edges]
        device_graph.add_edges_from(intermodule_edges)
        return device_graph

    def _build_modules(self, module_graphs: List[nx.Graph]) -> Tuple:
        """Construct arquin.Module objects for each of the provided module graphs."""
        modules = []
        d2m_p2p_mapping, m2d_p2p_mapping = {}, {}
        device_qubit_counter = 0
        for module_index, module_graph in enumerate(module_graphs):
            module = arquin.Module(graph=module_graph, module_index=module_index)
            modules.append(module)
            for qubit in module.qubits:
                d2m_p2p_mapping[device_qubit_counter] = (module_index,qubit)
                m2d_p2p_mapping[(module_index, qubit)] = device_qubit_counter
                device_qubit_counter += 1
        return modules, d2m_p2p_mapping, m2d_p2p_mapping

    def _construct_qubit_graph(self) -> nx.Graph:
        """Graph containing all physical qubits within the device"""
        graph = nx.Graph()

        # Add all local edges
        for idx, module in enumerate(self.modules):
            local_edges = [
                [self.m2d_p2p_mapping[(idx, v1)], self.m2d_p2p_mapping[(idx, v2)]] for v1, v2 in module.graph.edges
            ]
            graph.add_edges_from(local_edges)

        # Add all global edges
        intermodule_edges = [
            [self.m2d_p2p_mapping[tuple(v1)], self.m2d_p2p_mapping[tuple(v2)]]
            for v1, v2 in self.global_edges
        ]
        graph.add_edges_from(intermodule_edges)

        return graph
