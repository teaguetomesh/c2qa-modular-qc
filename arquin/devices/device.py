import abc
from typing import Dict, List

import networkx as nx


class Device:
    """Class representing a single quantum computer.

    Provides the properties ``modules``, ``num_modules``, and ``module_sizes``.

    Concrete subclasses must implement the abstract ``build()`` function
    to construct a NetworkX graph representing the topology of the device. The
    nodes of the device graph represent individual modules.
    """

    def __init__(self, modules: List["arquin.module.Module"], global_edges: Dict = None) -> None:
        """Construct a new Device object

        Input
        -----
        modules - A list of the modules contained within this device
        global_edges - (Optional) A dictionary indicating the module connectivity. The keys of the dictionary are tuples
            corresponding to indices within the module list. The values are also tuples but correspond to the indices
            of the specific qubits within each module that form the inter-module edge. If no global_edges is given, the default
            is to connect the modules linearly with the first and last qubits of each module forming the inter-module edges.
            For example, a device where qubit 5 of module 0 is connected to qubit 1 of module 1 would be written as:
                global_edges = {(0,1):(5,1)}
        """
        self.modules = modules
        self.num_modules = len(self.modules)
        self.module_sizes = [module.num_qubits for module in self.modules]
        if global_edges:
            self.global_edges = global_edges
        else:
            global_edges = {}
            for i in range(self.num_modules - 1):
                global_edges[(i, i+1)] = (self.modules[i].qubits[-1], self.modules[i+1].qubits[0])

    @abc.abstractmethod
    def build(self) -> nx.Graph:
        """Returns a NetworkX Graph representing the connections between modules"""

    def get_qubits(self) -> List[int]:
        """NOTE: writing this as a getter function for now. Can move it to a class variable
        if we end up using it a lot.
        """
        qubits = []
        for module in self.modules:
            qubits.extend(module.qubits)
        return qubits

    def get_qubit_graph(self) -> nx.Graph:
        """Graph containing all qubits within the device"""
        graph = nx.Graph()
        for module in self.modules:
            graph.add_edges_from(module.module_graph.edges())

        intermodule_edges = list(self.global_edges.values())
        graph.add_edges_from(intermodule_edges)

        return graph
