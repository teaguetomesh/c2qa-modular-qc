from typing import List

import networkx as nx

import arquin


class RingModule(arquin.module.Module):
    def __init__(self, qubits: List[int]) -> None:
        super().__init__(qubits)
        self.module_graph = self.build()

    def build(self) -> nx.Graph:
        """Return a NetworkX Graph corresponding to a Ring module.

        The topology of the Ring module connects the qubits in a circular
        chain.
        """
        module_graph = nx.Graph()
        edges = []

        # Ring
        for i in range(self.num_qubits):
            edges.append((self.qubits[i], self.qubits[(i + 1) % self.num_qubits]))

        module_graph.add_edges_from(edges)

        return module_graph
