import abc
from typing import List

import networkx as nx


class Device:
    """Class representing a single quantum computer.

    Provides the properties ``modules``, ``num_modules``, and ``module_sizes``.

    Concrete subclasses must implement the abstract ``build()`` function
    to construct a NetworkX graph representing the topology of the device. The
    nodes of the device graph represent individual modules.
    """

    def __init__(self, modules: List["arquin.module.Module"]) -> None:
        self.modules = modules
        self.num_modules = len(self.modules)
        self.module_sizes = [module.num_qubits for module in self.modules]

    @abc.abstractmethod
    def build(self) -> nx.Graph:
        """Returns a NetworkX Graph representing the connections between modules"""
