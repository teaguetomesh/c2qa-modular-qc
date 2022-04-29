import abc
from typing import Iterable

import networkx as nx

import arquin


class Device:
    """Class representing a single quantum computer."""

    def __init__(self, modules: Iterable[arquin.module.Module]) -> None:
        # TODO: finish implementing this class
        self.modules = modules
        self.num_modules = len(self.modules)
        self.module_sizes = [module.num_qubits for module in self.modules]

    @abc.abstractmethod
    def build(self) -> nx.Graph:
        """Returns a NetworkX Graph representing the connections between modules"""
