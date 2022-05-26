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
            
            print("Step 1: distribute the virtual gates in remaining_circuit to modules")
            vertex_weights, edges = arquin.converters.circuit_to_graph(circuit=remaining_circuit)
            circuit_graph = arquin.converters.edges_to_source_graph(
                edges=edges, vertex_weights=vertex_weights
            )
            # [print("Line {:d} {}".format(line_num,circuit_graph[line_num])) for line_num in circuit_graph]
            arquin.converters.write_source_graph_file(
                graph=circuit_graph, save_dir=self.work_dir, fname=self.circuit_name
            )
            arquin.comms.distribute_gates(
                source_fname=self.circuit_name, target_fname=self.device_name
            )
            distribution = arquin.comms.read_distribution_file(
                distribution_fname="%s_%s" % (self.circuit_name, self.device_name)
            )
            print("-" * 10)
            
            print("Step 2: assign the device_virtual_qubit to modules")
            arquin.comms.assign_device_virtual_qubits(
                distribution=distribution, circuit=remaining_circuit, device=self.device
            )
            print("-" * 10)

            print("Step 3: greedy construction of the module virtual circuits")
            next_circuit = arquin.comms.construct_module_virtual_circuits(
                circuit=remaining_circuit, device=self.device, distribution=distribution
            )
            print("-" * 10)

            print("Step 4: local compile")
            target_mp_2_mv_mappings = self.local_compile()
            print("-" * 10)

            print("Step 5: Insert Global communication")
            self.global_comm(target_mp_2_mv_mappings)
            print("-" * 10)
            exit(1)

            # Step 6: combine
            self.combine()
            print("output circuit depth %d" % self.output_dag.depth())
            # self.visualize(remaining_circuit=remaining_circuit, local_compiled_circuits=local_compiled_circuits, next_circuit=next_circuit)
            remaining_circuit = next_circuit
            recursion_counter += 1

    def global_comm(self, target_mp_2_mv_mappings: Dict) -> None:
        for module in self.device.modules:
            print(module.mp_2_mv_mapping)
            print(target_mp_2_mv_mappings[module.module_index])
        print("Inter module edges:", self.device.coarse_graph.edges)
        print(self.device.dv_2_mv_mapping)

    def local_compile(self) -> None:
        target_mp_2_mv_mappings = {}
        for module in self.device.modules:
            target_mp_2_mv_mapping = module.compile()
            target_mp_2_mv_mappings[module.module_index] = target_mp_2_mv_mapping
        return target_mp_2_mv_mappings

    def combine(self) -> None:
        for module in self.device.modules:
            print(self.device.dp_2_mp_mapping)
            print(self.device.dp_2_dv_mapping)
            print(module.mp_2_mv_mapping)
            print(module.circuit)
            self.output_circuit.compose(
                module.circuit,
                qubits=self.output_circuit.qubits[module.offset : module.offset + len(module.qubits)],
            )
            module.update_mapping()

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
