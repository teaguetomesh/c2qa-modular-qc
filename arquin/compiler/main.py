import copy, subprocess, os
from qiskit import QuantumCircuit
from qiskit.compiler import transpile
from qiskit.converters import circuit_to_dag, dag_to_circuit

from compiler.converters import edges_to_source_graph, circuit_to_graph, write_source_graph_file, write_target_graph_file, edges_to_coupling_map
from compiler.comms import distribute_gates, construct_local_circuits, assign_qubits, read_distribution_file

class ModularCompiler:
    def __init__(self, circuit, circuit_name, device, device_name):
        self.circuit = circuit
        self.circuit_name = circuit_name
        self.device = device
        self.device_name = device_name
        output_circuit = QuantumCircuit(self.circuit.width())
        self.output_dag = circuit_to_dag(output_circuit)
        self.work_dir = './workspace/'
        if os.path.exists(self.work_dir):
            subprocess.run(['rm','-rf',self.work_dir])
        os.makedirs(self.work_dir)
    
    def run(self):
        device_graph = edges_to_source_graph(edges=self.device.abstract_inter_edges,vertex_weights=None)
        write_target_graph_file(graph=device_graph, save_dir=self.work_dir, fname=self.device_name)

        curr_circuit = copy.deepcopy(self.circuit)
        recursion_counter = 0
        while curr_circuit.size()>0:
            print('*'*20,'Recursion %d'%recursion_counter,'*'*20)
            print('curr_circuit size %d'%curr_circuit.size())
            vertex_weights, edges= circuit_to_graph(circuit=curr_circuit)
            circuit_graph = edges_to_source_graph(edges=edges, vertex_weights=vertex_weights)
            write_source_graph_file(graph=circuit_graph, save_dir=self.work_dir, fname=self.circuit_name)
            distribute_gates(source_fname=self.circuit_name,target_fname=self.device_name)
            distribution = read_distribution_file(distribution_fname='%s_%s'%(self.circuit_name,self.device_name))
            module_qubit_assignments = assign_qubits(distribution=distribution, circuit=curr_circuit, device=self.device)
            self.global_comm(module_qubit_assignments)
            next_circuit, local_circuits = construct_local_circuits(circuit=curr_circuit, device=self.device, distribution=distribution)
            local_compiled_circuits = self.local_compile(local_circuits=local_circuits)
            self.combine(local_compiled_circuits=local_compiled_circuits)
            print('output circuit depth %d'%self.output_dag.depth())
            self.visualize(curr_circuit=curr_circuit, local_compiled_circuits=local_compiled_circuits, next_circuit=next_circuit)
            curr_circuit = next_circuit
            recursion_counter += 1
    
    def local_compile(self, local_circuits):
        local_compiled_circuits = []
        for local_circuit, module in zip(local_circuits,self.device.modules):
            coupling_map = edges_to_coupling_map(module.edges)
            local_compiled_circuit = transpile(local_circuit,coupling_map=coupling_map,layout_method='sabre',routing_method='sabre')
            module.update_mapping(circuit=local_compiled_circuit)
            local_compiled_circuits.append(local_compiled_circuit)
        return local_compiled_circuits
    
    def combine(self, local_compiled_circuits):
        for local_compiled_circuit, module in zip(local_compiled_circuits, self.device.modules):
            local_compiled_dag = circuit_to_dag(local_compiled_circuit)
            self.output_dag.compose(local_compiled_dag,
                qubits=self.output_dag.qubits[module.offset:module.offset+len(module.qubits)])
    
    def global_comm(self, module_qubit_assignments):
        if self.output_dag.size()==0:
            for module_idx in module_qubit_assignments:
                self.device.modules[module_idx].mapping=module_qubit_assignments[module_idx]
        else:
            for module_idx in module_qubit_assignments:
                module = self.device.modules[module_idx]
                curr_mapping = [self.circuit.qubits.index(qubit) for qubit in module.mapping]
                desired_mapping = [self.circuit.qubits.index(qubit) for qubit in module_qubit_assignments[module_idx]]
                print('Module {:d} {} --> {}'.format(
                    module_idx,
                    curr_mapping,
                    desired_mapping
                ))
            print('Abstract inter module edges:',self.device.abstract_inter_edges)
            exit(1)

    def visualize(self, curr_circuit, local_compiled_circuits, next_circuit):
        curr_circuit.draw(output='text',filename='./workspace/curr_circuit.txt')
        module_counter = 0
        for module, local_compiled_circuit in zip(self.device.modules,local_compiled_circuits):
            local_compiled_circuit.draw(output='text',filename='./workspace/module_%d.txt'%module_counter)
            module_counter += 1
        next_circuit.draw(output='text',filename='./workspace/next_circuit.txt')
        output_circuit = dag_to_circuit(self.output_dag)
        output_circuit.draw(output='text',filename='./workspace/output.txt')