import networkx as nx
import numpy as np
from arquin.modules.generic_module import Module

class Device:
    def __init__(self, device_graph, module_graphs):
        '''
        device_graph: graph of the device. Abstract each module as a node in the graph. Graph edges are the inter-module edges.
        module_graphs: graphs of each module
        '''
        assert len(module_graphs) == len(device_graph.nodes)
        self.modules = self._build_modules(module_graphs=module_graphs)
        self.abstract_inter_edges = device_graph.edges
        self.inter_edges, self.intra_edges = self._connect_modules()
        self.size = sum([len(module.qubits) for module in self.modules])
    
    def _build_modules(self, module_graphs):
        modules = []
        offset = 0
        for module_graph in module_graphs:
            module_edges = module_graph.edges
            module_graph = nx.Graph(module_edges)
            module = Module(graph=module_graph, offset=offset)
            modules.append(module)
            offset += len(module.qubits)
        return modules
    
    def _connect_modules(self):
        inter_edges = []
        for global_edge in self.abstract_inter_edges:
            module_l, module_r = global_edge
            module_l_qubit = np.random.choice(self.modules[module_l].qubits)
            module_r_qubit = np.random.choice(self.modules[module_r].qubits)
            inter_edges.append([module_l_qubit, module_r_qubit])
        intra_edges = []
        for module in self.modules:
            intra_edges += module.edges
        return inter_edges, intra_edges