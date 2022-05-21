import networkx as nx
import numpy as np

from arquin.module.main import Module

class Device:
    def __init__(self, device_graph, module_graphs):
        '''
        device_graph: graph of the device. Each module is a node. Inter-module connections are the edges.
        module_graphs: list of graphs of each module
        '''
        assert len(module_graphs) == device_graph.size()
        self.modules = self._build_modules(module_graphs=module_graphs)
        self.global_edges, self.local_edges = self._connect_modules(device_graph=device_graph)
        self.abstract_global_edges = device_graph.edges
        self.size = sum([module.size for module in self.modules])
    
    def _build_modules(self, module_graphs):
        modules = []
        offset = 0
        for module_graph in module_graphs:
            module = Module(graph=module_graph, offset=offset)
            offset += module.size
            modules.append(module)
        return modules
    
    def _connect_modules(self, device_graph):
        global_edges = []
        for global_edge in device_graph.edges:
            module_idx_l, module_idx_r = global_edge
            module_l_qubit = np.random.choice(self.modules[module_idx_l].qubits) + self.modules[module_idx_l].offset
            module_r_qubit = np.random.choice(self.modules[module_idx_r].qubits) + self.modules[module_idx_r].offset
            global_edges.append([module_l_qubit, module_r_qubit])
        local_edges = []
        for module in self.modules:
            module_edges_with_offset = []
            for edge in module.edges:
                edge_with_offset = [edge[0] + module.offset, edge[1] + module.offset]
                module_edges_with_offset.append(edge_with_offset)
            local_edges += module_edges_with_offset
        return global_edges, local_edges