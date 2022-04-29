from module.ring import RingModule
from module.helper_fun import add_flip_edges
import numpy as np

class Ring():
    def __init__(self, num_modules, module_size):
        self.num_modules = num_modules
        self.module_size = module_size
        self.build()
    
    def build(self):
        modules = [RingModule(num_qubits=self.module_size,offset=module_idx*self.module_size)
        for module_idx in range(self.num_modules)]

        self.edges = []
        self.global_edges = []
        # Ring
        for module_idx in range(self.num_modules):
            module = modules[module_idx]
            right_qubit = int(np.floor(np.median(module.qubits)))
            next_module_idx = (module_idx+1)%self.num_modules
            next_module = modules[next_module_idx]
            next_left_qubit = np.min(next_module.qubits)
            self.edges.append([right_qubit,next_left_qubit])
            self.global_edges.append([module_idx,next_module_idx])
        
        self.qubits = set()
        for module in modules:
            self.edges += module.edges
            self.qubits.update(module.qubits)
        self.edges = add_flip_edges(edges=self.edges)
        self.qubits = list(self.qubits)