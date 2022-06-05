from __future__ import annotations

from typing import Dict, List

import networkx as nx
import numpy as np
import qiskit
import matplotlib.pyplot as plt

import arquin


class Device:
    """Class representing a single quantum computer.

    Provides the properties ``graph``, ``modules``, ``global_edges``, ``local_edges``, and ``size``.

    DEFINE THE DIFFERENT GRAPHS AND QUBIT REPRESENTATIONS HERE
    The nodes of the device graph represent individual modules.
    dp_2_mp_mapping: device physical to module virtual mapping
    mp_2_dp_mapping: module physical to device physical mapping
    dp_2_dv_mapping: device physical to device virtual mapping
    dv_2_dp_mapping: device virtual to device physical mapping
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

        self.coarse_graph = self._build_coarse_device_graph(global_edges)
        assert len(module_graphs) == self.coarse_graph.number_of_nodes()
        self.modules, self.dp_2_mp_mapping = self._build_modules(module_graphs)
        self.mp_2_dp_mapping = arquin.converters.reverse_dict(self.dp_2_mp_mapping)
        self.fine_graph = self._build_fine_device_graph(global_edges)
        self.size = sum([module.size for module in self.modules])
        self.dv_2_mv_mapping = None
        self.mv_2_dv_mapping = None
        self.dp_2_dv_mapping = None
        self.dv_2_dp_mapping = None

    def _build_coarse_device_graph(self, global_edges) -> nx.Graph:
        """Construct the device graph using the global edges."""
        device_graph = nx.MultiGraph()
        intermodule_edges = [[edge[0][0], edge[1][0]] for edge in global_edges]
        device_graph.add_edges_from(intermodule_edges)
        return device_graph

    def _build_modules(self, module_graphs: List[nx.Graph]) -> tuple:
        """Construct arquin.Module objects for each of the provided module graphs."""
        modules = []
        dp_2_mp_mapping = {}
        device_physical_qubit = 0
        for module_index, module_graph in enumerate(module_graphs):
            module = arquin.Module(graph=module_graph, index=module_index)
            modules.append(module)
            for module_physical_qubit in range(module.size):
                dp_2_mp_mapping[device_physical_qubit] = (module_index, module_physical_qubit)
                device_physical_qubit += 1
        return modules, dp_2_mp_mapping

    def _build_fine_device_graph(self, global_edges) -> nx.Graph:
        """Graph containing all physical qubits within the device"""
        graph = nx.Graph()

        # Add all local edges
        for idx, module in enumerate(self.modules):
            local_edges = [
                [self.mp_2_dp_mapping[(idx, v1)], self.mp_2_dp_mapping[(idx, v2)]]
                for v1, v2 in module.graph.edges
            ]
            graph.add_edges_from(local_edges)

        # Add all global edges
        intermodule_edges = [
            [self.mp_2_dp_mapping[tuple(v1)], self.mp_2_dp_mapping[tuple(v2)]]
            for v1, v2 in global_edges
        ]
        graph.add_edges_from(intermodule_edges)

        return graph

    def plot(self, save_dir):
        nx.draw(self.fine_graph, with_labels=True)
        plt.savefig("%s/fine_device.pdf" % (save_dir))
        plt.close()
        nx.draw(self.coarse_graph, with_labels=True)
        plt.savefig("%s/coarse_device.pdf" % (save_dir))
        plt.close()
