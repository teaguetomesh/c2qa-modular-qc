import abc
from typing import List

import networkx as nx


class Module:
    """Class representing a single module within a distributed quantum computer.

    Provides properties ``num_qubits``, ``qubits``.

    Concrete sublcasses must implement the abstract ``build()``
    function to construct the specific module topology they want. The nodes of
    the module graph represent individual qubits.
    """

    def __init__(self, qubits: List[int]) -> None:
        self.qubits = qubits
        self.num_qubits = len(self.qubits)

    @abc.abstractmethod
    def build(self) -> nx.Graph:
        """Returns a NetworkX Graph with edges between connected qubits"""
