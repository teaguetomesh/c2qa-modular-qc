import copy
from qiskit.converters import circuit_to_dag

class Module:
    def __init__(self, graph, offset):
        '''
        Networkx graph for the module connectivity
        '''
        self.qubits = [node+offset for node in graph.nodes]
        self.edges = [[edge[0]+offset, edge[1]+offset] for edge in graph.edges]
        self.offset = offset
        self.mapping = [] # Index is the module qubit, value is the circuit/device qubit
    
    def update_mapping(self, circuit):
        '''
        Update the mapping based on the SWAPs in the circuit
        '''
        # print(circuit)
        # print('Mapping before compile :',self.mapping)
        new_initial_mapping = copy.deepcopy(self.mapping)
        for module_physical_qubit in circuit._layout.get_physical_bits():
            module_virtual_qubit = circuit._layout.get_physical_bits()[module_physical_qubit]
            # print(module_physical_qubit, module_virtual_qubit)
            new_initial_mapping[module_physical_qubit] = self.mapping[circuit.qubits.index(module_virtual_qubit)]
        self.mapping = new_initial_mapping
        # print('Mapping after compile :',self.mapping)
        dag = circuit_to_dag(circuit)
        for gate in dag.topological_op_nodes():
            if gate.op.name =='swap':
                physical_qubits = [circuit.qubits.index(qarg) for qarg in gate.qargs]
                device_qubit_0, device_qubit_1 = [self.mapping[physical_qubit] for physical_qubit in physical_qubits]
                self.mapping[physical_qubits[0]] = device_qubit_1
                self.mapping[physical_qubits[1]] = device_qubit_0
        # print('Final mapping after SWAPs :',self.mapping)
        # print('*'*20)