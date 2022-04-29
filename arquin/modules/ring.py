import networkx as nx

import arquin


class RingModule(arquin.module.Module):
    def __init__(self, num_qubits: int) -> None:
        super().__init__(num_qubits)
        self.module_graph = self.build()

    def build(self) -> nx.Graph:
        """Return a NetworkX Graph corresponding to a Ring module.

        The topology of the Ring module connects the qubits in a circular
        chain.
        """
        edges = []

        # Ring
        for qubit in self.qubits:
            edges.append([qubit, (qubit + 1) % self.num_qubits])

        return nx.Graph().add_edges_from(edges)
