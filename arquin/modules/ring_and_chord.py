from typing import List

import networkx as nx

import arquin


class RingAndChordModule(arquin.module.Module):
    def __init__(self, qubits: List[int], offset: int) -> None:
        super().__init__(qubits)
        self._offset = offset
        self.module_graph = self.build()

    def build(self) -> nx.Graph:
        """Return a NetworkX Graph corresponding to a Ring module.

        The topology of the RingAndChord module connects the qubits in a circular
        chain, with some chords existing between pairs of qubits separated
        by a distance equal to the ``offset``.
        """
        module_graph = nx.Graph()
        edges = []

        # Ring
        for i in range(self.num_qubits):
            edges.append((self.qubits[i], self.qubits[(i + 1) % self.num_qubits]))

        # Chords
        chords = []
        start_qubit_idx = 0
        while start_qubit_idx < self.num_qubits - self._offset:
            chords.append(
                (self.qubits[start_qubit_idx], self.qubits[start_qubit_idx + self._offset])
            )
            start_qubit_idx += self._offset + 1

        module_graph.add_edges_from(edges + chords)

        return module_graph
