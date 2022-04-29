import networkx as nx

import arquin


class RingAndChordModule(arquin.module.Module):
    def __init__(self, num_qubits: int, offset: int) -> None:
        super().__init__(num_qubits)
        self._offset = offset
        self.module_graph = self.build()

    def build(self) -> nx.Graph:
        """Return a NetworkX Graph corresponding to a Ring module.

        The topology of the RingAndChord module connects the qubits in a circular
        chain, with some chords existing between pairs of qubits separated
        by a distance equal to the ``offset``.
        """
        edges = []

        # Ring
        for qubit in self.qubits:
            edges.append([qubit, (qubit + 1) % self.num_qubits])

        # Chords
        chords = []
        for q1, q2 in edges:
            chord = [q1 + self._offset, q2 + self._offset]
            chords.append(chord)

        return nx.Graph().add_edges_from(edges)
