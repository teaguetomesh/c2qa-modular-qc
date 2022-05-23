import networkx as nx
import numpy as np
from qiskit.converters import circuit_to_dag
from qiskit import QuantumCircuit

from arquin.module.main import Module

class Device:
    def __init__(self, device_graph, module_graphs):
        '''
        device_graph: graph of the device. Each module is a node. Inter-module connections are the edges.
        module_graphs: list of graphs of each module
        '''
        assert len(module_graphs) == device_graph.size()
        self.coarse_global_edges = device_graph.edges
        self.size = sum([module_graph.size() for module_graph in module_graphs])
        circuit = QuantumCircuit(self.size)
        self.dag = circuit_to_dag(circuit)
        self.modules, self.device_to_module_physical = self._build_modules(module_graphs=module_graphs)
        self.fine_edges = self._connect_modules()
    
    def _build_modules(self, module_graphs):
        modules = []
        device_to_module_physical = []
        for module_idx, module_graph in enumerate(module_graphs):
            module = Module(graph=module_graph, module_idx=module_idx)
            for qubit in module.qubits:
                device_to_module_physical.append((module_idx,qubit))
            modules.append(module)
        return modules, device_to_module_physical
    
    def _connect_modules(self):
        global_edges = []
        for coarse_global_edge in self.coarse_global_edges:
            module_idx_l, module_idx_r = coarse_global_edge
            
            module_qubit_l = np.random.choice(self.modules[module_idx_l].qubits)
            device_qubit_l = self.device_to_module_physical.index((module_idx_l,module_qubit_l))

            module_qubit_r = np.random.choice(self.modules[module_idx_r].qubits)
            device_qubit_r = self.device_to_module_physical.index((module_idx_r,module_qubit_r))

            global_edges.append([device_qubit_l, device_qubit_r])

        local_edges = []
        for module_idx, module in enumerate(self.modules):
            for edge in module.edges:
                module_qubit_0, module_qubit_1 = edge
                device_qubit_0 = self.device_to_module_physical.index((module_idx, module_qubit_0))
                device_qubit_1 = self.device_to_module_physical.index((module_idx, module_qubit_1))
                local_edges.append([device_qubit_0,device_qubit_1])
        fine_edges = global_edges + local_edges
        return fine_edges