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

        self.modules = self._build_modules(module_graphs=module_graphs)

        # Nodes are device qubits, edges are (qubit_i, qubit_j)
        self.physical_qubit_graph = self._construct_qubit_graph()

        self.size = sum([module.size for module in self.modules])

    def _build_device_graph(self) -> nx.Graph:
        """Construct the device graph using the global edges."""
        device_graph = nx.Graph()
        intermodule_edges = [[edge[0][0], edge[1][0]] for edge in self.global_edges]
        device_graph.add_edges_from(intermodule_edges)
        return device_graph

    def _build_modules(self, module_graphs):
        """Construct arquin.Module objects for each of the provided module graphs."""
        modules = []
        offset = 0
        for module_graph in module_graphs:
            module = arquin.Module(graph=module_graph, offset=offset)
            offset += module.size
            modules.append(module)
        return modules

    def _construct_qubit_graph(self) -> nx.Graph:
        """Graph containing all physical qubits within the device"""
        graph = nx.Graph()

        # Add all local edges
        for module in self.modules:
            local_edges = [
                [v1 + module.offset, v2 + module.offset] for v1, v2 in module.graph.edges
            ]
            graph.add_edges_from(local_edges)

        # Add all global edges
        intermodule_edges = [
            [self.module_to_device_qubit(v1), self.module_to_device_qubit(v2)]
            for v1, v2 in self.global_edges
        ]
        graph.add_edges_from(intermodule_edges)

        return graph

    def module_to_device_qubit(self, module_qubit: List[int, int]) -> int:
        """Convert a module format qubit to a device format qubit"""
        return module_qubit[1] + self.modules[module_qubit[0]].offset

    def device_to_module_qubit(self, device_qubit: int) -> List[int, int]:
        """Convert a device format qubit to a module format qubit"""

        temp_qubit_index = device_qubit
        module_index, qubit_index = -1, -1
        for i, module in enumerate(self.modules):
            temp_qubit_index -= module.size
            if temp_qubit_index < 0:
                module_index = i
                qubit_index = device_qubit - module.offset
                break

        assert module_index >= 0 and qubit_index >= 0

        return [module_index, qubit_index]
