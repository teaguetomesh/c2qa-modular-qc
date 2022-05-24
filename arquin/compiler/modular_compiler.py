from __future__ import annotations

import copy
import os
import subprocess
from typing import Dict, List

import qiskit

import arquin


class ModularCompiler:
    def __init__(
        self,
        circuit: qiskit.QuantumCircuit,
        circuit_name: str,
        device: arquin.device.Device,
        device_name: str,
    ) -> None:
        self.circuit = circuit
        self.circuit_name = circuit_name
        self.device = device
        self.device_name = device_name
        output_circuit = qiskit.QuantumCircuit(self.circuit.width())
        self.output_dag = qiskit.converters.circuit_to_dag(output_circuit)
        self.work_dir = "./workspace/"
        if os.path.exists(self.work_dir):
            subprocess.run(["rm", "-rf", self.work_dir])
        os.makedirs(self.work_dir)

    def run(self) -> None:
        # Step 0: convert the device topology graph to SCOTCH format
        device_graph = arquin.converters.edges_to_source_graph(
            edges=self.device.graph.edges, vertex_weights=None
        )
        arquin.converters.write_target_graph_file(
            graph=device_graph, save_dir=self.work_dir, fname=self.device_name
        )

        remaining_circuit = copy.deepcopy(self.circuit)
        recursion_counter = 0
        while remaining_circuit.size() > 0:
            print("*" * 20, "Recursion %d" % recursion_counter, "*" * 20)
            print("remaining_circuit size %d" % remaining_circuit.size())
            # Step 1: convert the remaining circuit to SCOTCH format
            vertex_weights, edges = arquin.converters.circuit_to_graph(circuit=remaining_circuit)
            circuit_graph = arquin.converters.edges_to_source_graph(
                edges=edges, vertex_weights=vertex_weights
            )
            arquin.converters.write_source_graph_file(
                graph=circuit_graph, save_dir=self.work_dir, fname=self.circuit_name
            )

            # Step 2: distribute the gates and assign the qubits to modules
            arquin.comms.distribute_gates(source_fname=self.circuit_name, target_fname=self.device_name)
            distribution = arquin.comms.read_distribution_file(
                distribution_fname="%s_%s" % (self.circuit_name, self.device_name)
            )
            module_qubit_assignments = arquin.comms.assign_qubits(
                distribution=distribution, circuit=remaining_circuit, device=self.device
            )

            # Step 3: Global communication (skipped in the first recursion)
            self.global_comm(module_qubit_assignments)
            exit(1)

            # Step 4: greedy construction of the local circuits
            next_circuit, local_circuits = arquin.comms.construct_local_circuits(
                circuit=remaining_circuit, device=self.device, distribution=distribution
            )

            # Step 5: local compile and combine
            local_compiled_circuits = self.local_compile(local_circuits=local_circuits)
            self.combine(local_compiled_circuits=local_compiled_circuits)
            print("output circuit depth %d" % self.output_dag.depth())
            # self.visualize(remaining_circuit=remaining_circuit, local_compiled_circuits=local_compiled_circuits, next_circuit=next_circuit)
            remaining_circuit = next_circuit
            recursion_counter += 1
    
    def global_comm(self, module_qubit_assignments: Dict) -> None:
        if self.output_dag.size() == 0:
            for module_idx in module_qubit_assignments:
                for qubit in module_qubit_assignments[module_idx]:
                    self.device.modules[module_idx].add_device_virtual_qubit(qubit)
                print("Module %d: "%module_idx,self.device.modules[module_idx].m2d_p2v_mapping)
        else:
            for module_idx in module_qubit_assignments:
                module = self.device.modules[module_idx]
                curr_mapping = [self.circuit.qubits.index(qubit) for qubit in module.mapping]
                desired_mapping = [
                    self.circuit.qubits.index(qubit)
                    for qubit in module_qubit_assignments[module_idx]
                ]
                print("Module {:d} {} --> {}".format(module_idx, curr_mapping, desired_mapping))
            print("Abstract inter module edges:", self.device.abstract_inter_edges)
            exit(1)

    def local_compile(
        self, local_circuits: List[qiskit.QuantumCircuit]
    ) -> List[qiskit.QuantumCircuit]:
        local_compiled_circuits = []
        for local_circuit, module in zip(local_circuits, self.device.modules):
            coupling_map = arquin.converters.edges_to_coupling_map(module.edges)
            local_compiled_circuit = qiskit.compiler.transpile(
                local_circuit,
                coupling_map=coupling_map,
                layout_method="sabre",
                routing_method="sabre",
            )
            module.update_mapping(circuit=local_compiled_circuit)
            local_compiled_circuits.append(local_compiled_circuit)
        return local_compiled_circuits

    def combine(self, local_compiled_circuits: List[qiskit.QuantumCircuit]) -> None:
        for local_compiled_circuit, module in zip(local_compiled_circuits, self.device.modules):
            local_compiled_dag = qiskit.converters.circuit_to_dag(local_compiled_circuit)
            self.output_dag.compose(
                local_compiled_dag,
                qubits=self.output_dag.qubits[module.offset : module.offset + len(module.qubits)],
            )

    def visualize(
        self,
        curr_circuit: qiskit.QuantumCircuit,
        local_compiled_circuits: List[qiskit.QuantumCircuit],
        next_circuit: qiskit.QuantumCircuit,
    ) -> None:
        curr_circuit.draw(output="text", filename="./workspace/curr_circuit.txt")
        module_counter = 0
        for module, local_compiled_circuit in zip(self.device.modules, local_compiled_circuits):
            local_compiled_circuit.draw(
                output="text", filename="./workspace/module_%d.txt" % module_counter
            )
            module_counter += 1
        next_circuit.draw(output="text", filename="./workspace/next_circuit.txt")
        output_circuit = qiskit.converters.dag_to_circuit(self.output_dag)
        output_circuit.draw(output="text", filename="./workspace/output.txt")
