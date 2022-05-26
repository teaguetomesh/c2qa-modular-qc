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
        self.output_circuit = qiskit.QuantumCircuit(self.circuit.width())
        self.work_dir = "./workspace/"
        if os.path.exists(self.work_dir):
            subprocess.run(["rm", "-rf", self.work_dir])
        os.makedirs(self.work_dir)

    def run(self) -> None:
        # Step 0: convert the device topology graph to SCOTCH format
        device_graph = arquin.converters.edges_to_source_graph(
            edges=self.device.coarse_graph.edges, vertex_weights=None
        )
        arquin.converters.write_target_graph_file(
            graph=device_graph, save_dir=self.work_dir, fname=self.device_name
        )

        remaining_circuit = copy.deepcopy(self.circuit)
        recursion_counter = 0
        while remaining_circuit.size() > 0:
            print("*" * 20, "Recursion %d" % recursion_counter, "*" * 20)
            print("remaining_circuit size %d" % remaining_circuit.size())
            
            # Step 1: distribute the virtual gates in remaining_circuit to modules
            vertex_weights, edges = arquin.converters.circuit_to_graph(circuit=remaining_circuit)
            circuit_graph = arquin.converters.edges_to_source_graph(
                edges=edges, vertex_weights=vertex_weights
            )
            arquin.converters.write_source_graph_file(
                graph=circuit_graph, save_dir=self.work_dir, fname=self.circuit_name
            )
            arquin.comms.distribute_gates(
                source_fname=self.circuit_name, target_fname=self.device_name
            )
            distribution = arquin.comms.read_distribution_file(
                distribution_fname="%s_%s" % (self.circuit_name, self.device_name)
            )
            
            # Step 2: assign the device_virtual_qubit to modules
            arquin.comms.assign_device_virtual_qubits(
                distribution=distribution, circuit=remaining_circuit, device=self.device
            )
            for device_virtual_qubit in self.device.dv_2_mv_mapping:
                module_index, module_virtual_qubit = self.device.dv_2_mv_mapping[device_virtual_qubit]
                print("{} --> Module {:d} {}".format(device_virtual_qubit,module_index,module_virtual_qubit))

            # Step 3: greedy construction of the module virtual circuits
            next_circuit = arquin.comms.construct_module_virtual_circuits(
                circuit=remaining_circuit, device=self.device, distribution=distribution
            )
            print(next_circuit.size())
            exit(1)

            # Step 4: local compile
            self.local_compile(recursion_counter)

            # Step 5: Global communication (skipped in the first recursion)
            self.global_comm(module_qubit_assignments, recursion_counter)

            # Step 6: combine
            self.combine()
            print("output circuit depth %d" % self.output_dag.depth())
            # self.visualize(remaining_circuit=remaining_circuit, local_compiled_circuits=local_compiled_circuits, next_circuit=next_circuit)
            remaining_circuit = next_circuit
            recursion_counter += 1

    def global_comm(self, module_qubit_assignments: Dict, recursion_counter: int) -> None:
        if recursion_counter == 0:
            for module_idx in module_qubit_assignments:
                module = self.device.modules[module_idx]
                for module_physical_qubit, device_virtual_qubit in enumerate(module_qubit_assignments[module_idx]):
                    device_physical_qubit = self.device.mp_2_dp_mapping[(module_idx,module_physical_qubit)]
                    module_virtual_qubit = module.circuit.qubits[module_physical_qubit]
                    self.device.dp_2_dv_mapping[device_physical_qubit] = device_virtual_qubit
                    self.device.dv_2_dp_mapping[device_virtual_qubit] = device_physical_qubit
                    module.mp_2_mv_mapping[module_physical_qubit] = module_virtual_qubit
                    print("{} --> Device physical {:d} (Module {:d} physical {:d}) --> {}".format(
                        device_virtual_qubit, device_physical_qubit, module_idx, module_physical_qubit, module_virtual_qubit
                    ))
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
        print("-" * 10)

    def local_compile(self, recursion_counter:int) -> None:
        for module in self.device.modules:
            module.compile(has_initial_layout=recursion_counter>0)
            module.update_mapping()
            print("-" * 10)

    def combine(self) -> None:
        for module in self.device.modules:
            print(self.device.dp_2_mp_mapping)
            print(self.device.dp_2_dv_mapping)
            print(module.mp_2_mv_mapping)
            print(module.circuit)
            exit(1)
            self.output_circuit.compose(
                module.circuit,
                qubits=self.output_circuit.qubits[module.offset : module.offset + len(module.qubits)],
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
