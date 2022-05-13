from typing import Dict

import networkx as nx
import numpy as np

import arquin


class Loop(arquin.device.Device):
    """A quantum computer composed of many RingAndChordModule connected in a circle."""

    def __init__(
        self, num_modules: int, module_size: int, global_edges: Dict = None, module_offset: int = 2
    ) -> None:
        modules = [
            arquin.ring_and_chord.RingAndChordModule(
                qubits=list(np.arange(i * module_size, (i + 1) * module_size)), offset=module_offset
            )
            for i in range(num_modules)
        ]

        if not global_edges:
            # Default module connectivity for Loop device
            global_edges = {}
            for i in range(num_modules):
                global_edges[(i, (i + 1) % num_modules)] = (
                    modules[i].qubits[modules[i].num_qubits // 2],
                    modules[(i + 1) % num_modules].qubits[0],
                )

        super().__init__(modules, global_edges=global_edges)
        self.device_graph = self.build()

    def build(self) -> nx.Graph:
        device_graph = nx.Graph()
        device_graph.add_edges_from(list(self.global_edges.keys()))
        return device_graph
