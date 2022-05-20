import networkx as nx
import numpy as np

from arquin.module.main import Module

class Device:
    def __init__(self, device_graph, module_graphs):
        '''
        device_graph: graph of the device. Each module is a node. Inter-module connections are the edges.
        module_graphs: list of graphs of each module
        '''
        assert len(module_graphs) == len(device_graph.nodes)
        self.modules = self._build_modules(module_graphs=module_graphs)
        self.global_edges, self.local_edges = self._connect_modules(device_graph=device_graph)
        self.size = sum([module.dag.width() for module in self.modules])
    
    def _build_modules(self, module_graphs):
        modules = []
        for module_idx, module_graph in enumerate(module_graphs):
            module = Module(graph=module_graph, index=module_idx)
            modules.append(module)
        return modules
    
    def _connect_modules(self, device_graph):
        global_edges = []
        for global_edge in device_graph.edges:
            module_l, module_r = global_edge
            module_l_qubit = np.random.choice(self.modules[module_l].dag.qubits)
            module_r_qubit = np.random.choice(self.modules[module_r].dag.qubits)
            global_edges.append([module_l_qubit, module_r_qubit])
        local_edges = []
        for module in self.modules:
            local_edges += module.edges
        return global_edges, local_edges