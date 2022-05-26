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
        self.virtual_circuit = circuit
        self.circuit_name = circuit_name
        self.device = device
        self.device_name = device_name
        self.physical_circuit = qiskit.QuantumCircuit(self.device.size)
        self.work_dir = "./workspace/"
        if os.path.exists(self.work_dir):
            subprocess.run(["rm", "-rf", self.work_dir])
        os.makedirs(self.work_dir)

    def run(self) -> None:
        print("Step 0: convert the device topology graph to SCOTCH format")
        device_graph = arquin.converters.edges_to_source_graph(
            edges=self.device.coarse_graph.edges, vertex_weights=None
        )
        arquin.converters.write_target_graph_file(
            graph=device_graph, save_dir=self.work_dir, fname=self.device_name
        )

        remaining_virtual_circuit = copy.deepcopy(self.virtual_circuit)
        recursion_counter = 0
        while remaining_virtual_circuit.size() > 0:
            print("*" * 20, "Recursion %d" % recursion_counter, "*" * 20)
            print("remaining_virtual_circuit size %d" % remaining_virtual_circuit.size())

            print("Step 1: Distribute the virtual gates in remaining_virtual_circuit to modules")
            vertex_weights, edges = arquin.converters.circuit_to_graph(
                circuit=remaining_virtual_circuit
            )
            circuit_graph = arquin.converters.edges_to_source_graph(
                edges=edges, vertex_weights=vertex_weights
            )
            arquin.converters.write_source_graph_file(
                graph=circuit_graph, save_dir=self.work_dir, fname=self.circuit_name
            )
            arquin.distribute.distribute_gates(
                source_fname=self.circuit_name, target_fname=self.device_name
            )
            distribution = arquin.distribute.read_distribution_file(
                distribution_fname="%s_%s" % (self.circuit_name, self.device_name)
            )
            print(distribution)
            print("-" * 10)

            print("Step 2: Assign the device_virtual_qubit to modules")
            arquin.distribute.assign_device_virtual_qubits(
                distribution=distribution, circuit=remaining_virtual_circuit, device=self.device
            )
            for device_virtual_qubit in self.device.dv_2_mv_mapping:
                module_index, module_virtual_qubit = self.device.dv_2_mv_mapping[
                    device_virtual_qubit
                ]
                print(
                    "{} --> Module {:d} {}".format(
                        device_virtual_qubit, module_index, module_virtual_qubit
                    )
                )
            print("-" * 10)

            print("Step 3: Insert global communication")
            self.global_comm(recursion_counter)
            print("-" * 10)

            print("Step 4: Greedy construction of the module virtual circuits")
            next_virtual_circuit = arquin.distribute.construct_module_virtual_circuits(
                circuit=remaining_virtual_circuit, device=self.device, distribution=distribution
            )
            print("-" * 10)

            print("Step 5: local compile")
            self.local_compile()
            print("-" * 10)

            print("Step 6: combine")
            self.combine()
            print("output circuit depth {:d}".format(self.physical_circuit.depth()))
            # self.visualize(remaining_virtual_circuit=remaining_virtual_circuit, local_compiled_circuits=local_compiled_circuits, next_circuit=next_circuit)
            remaining_virtual_circuit = next_virtual_circuit
            recursion_counter += 1

    def global_comm(self, recursion_counter: int) -> None:
        if recursion_counter == 0:
            print("First iteration does not need global communications")
            for module in self.device.modules:
                module.mv_2_dv_mapping = {}
            for module_virtual_qubit in self.device.mv_2_dv_mapping:
                device_virtual_qubit = self.device.mv_2_dv_mapping[module_virtual_qubit]
                module_index, module_virtual_qubit = module_virtual_qubit
                self.device.modules[module_index].mv_2_dv_mapping[
                    module_virtual_qubit
                ] = device_virtual_qubit
        else:
            print("Need global routing")
            exit(1)
        for module in self.device.modules:
            print(
                "Module {:d} mv_2_dv_mapping : {}".format(
                    module.module_index, module.mv_2_dv_mapping
                )
            )

    def local_compile(self) -> None:
        for module in self.device.modules:
            module.compile()
            module.update_mapping()
            print(
                "Module {:d} mp_2_mv_mapping : {}".format(
                    module.module_index, module.mp_2_mv_mapping
                )
            )

    def combine(self) -> None:
        print(self.device.mp_2_dp_mapping)
        for module in self.device.modules:
            print(module.physical_circuit)
            device_physical_qargs = [
                self.physical_circuit.qubits[
                    self.device.mp_2_dp_mapping[(module.module_index, module_physical_qubit)]
                ]
                for module_physical_qubit in range(module.size)
            ]
            print(device_physical_qargs)
            self.physical_circuit.compose(
                module.physical_circuit, qubits=device_physical_qargs, inplace=True
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
