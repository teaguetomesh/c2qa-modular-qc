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
        self.data_dir = "./data/%s/%s" % (self.device_name, self.circuit_name)
        if os.path.exists(self.data_dir):
            subprocess.run(["rm", "-rf", self.data_dir])
        os.makedirs(self.data_dir)

    def run(self, visualize: bool) -> None:
        print("Step 0: convert the device topology graph to SCOTCH format")
        device_graph = arquin.converters.edges_to_source_graph(
            edges=self.device.coarse_graph.edges, vertex_weights=None
        )
        arquin.converters.write_target_graph_file(graph=device_graph, save_dir=self.data_dir)

        self.device.virtual_circuit = self.virtual_circuit
        recursion_counter = 0
        while self.device.virtual_circuit.size() > 0:
            print("*" * 20, "Recursion %d" % recursion_counter, "*" * 20)
            print("Remaining virtual_circuit size %d" % self.device.virtual_circuit.size())

            print("Step 1: Distribute the virtual gates in remaining virtual_circuit to modules")
            vertex_weights, edges = arquin.converters.circuit_to_graph(
                circuit=self.device.virtual_circuit
            )
            circuit_graph = arquin.converters.edges_to_source_graph(
                edges=edges, vertex_weights=vertex_weights
            )
            arquin.converters.write_source_graph_file(graph=circuit_graph, save_dir=self.data_dir)
            arquin.distribute.distribute_gates(data_dir=self.data_dir)
            gate_distribution = arquin.distribute.read_distribution_file(data_dir=self.data_dir)
            print(gate_distribution)
            print("-" * 10)

            print("Step 2: Assign the device_virtual_qubit to modules")
            qubit_distribution = arquin.distribute.assign_device_virtual_qubits(
                gate_distribution=gate_distribution,
                device=self.device,
            )
            for module_index in qubit_distribution:
                print("Module {:d} : {}".format(module_index, qubit_distribution[module_index]))
                self.device.modules[module_index].virtual_circuit = qiskit.QuantumCircuit(len(qubit_distribution[module_index]))
            print("-" * 10)

            print("Step 3: Insert global communication")
            self.global_comm(qubit_distribution)
            print("-" * 10)

            print("Step 4: Greedy construction of the module virtual circuits")
            next_virtual_circuit = arquin.distribute.construct_module_virtual_circuits(
                device=self.device, gate_distribution=gate_distribution
            )
            for module in self.device.modules:
                print("Module {:d}".format(module.index))
                print(module.virtual_circuit)
            print("-" * 10)

            print("Step 5: local compile and combine")
            self.local_compile()
            self.combine()
            print("-" * 10)
            exit(1)
            if visualize:
                arquin.visualize.plot_recursion(
                    recursion_counter=recursion_counter,
                    device=self.device,
                    remaining_virtual_circuit=remaining_virtual_circuit,
                    distribution=distribution,
                    output_circuit=self.physical_circuit,
                )
            remaining_virtual_circuit = next_virtual_circuit
            recursion_counter += 1

    def global_comm(self, qubit_distribution: int) -> None:
        if self.device.mv_2_dv_mapping is None:
            print("First iteration does not need global communications")
            self.device.mv_2_dv_mapping = {}
            for module in self.device.modules:
                module.mv_2_dv_mapping = {}
                for qubit_counter in range(len(qubit_distribution[module.index])):
                    device_virtual_qubit = qubit_distribution[module.index][qubit_counter]
                    module_virtual_qubit = module.virtual_circuit.qubits[qubit_counter]
                    module.mv_2_dv_mapping[module_virtual_qubit] = device_virtual_qubit
                    self.device.mv_2_dv_mapping[(module.index, module_virtual_qubit)] = device_virtual_qubit
            self.device.dv_2_mv_mapping = arquin.converters.reverse_dict(self.device.mv_2_dv_mapping)
        else:
            print("Need global routing")
            exit(1)
        for device_virtual_qubit in self.device.virtual_circuit.qubits:
            module_index, module_virtual_qubit = self.device.dv_2_mv_mapping[device_virtual_qubit]
            print("{} --> Module {:d} {}".format(
                device_virtual_qubit, module_index, module_virtual_qubit
            ))

    def local_compile(self) -> None:
        for module in self.device.modules:
            module.compile()
            module.update_mapping()

    def combine(self) -> None:
        for module in self.device.modules:
            device_physical_qubits = [
                self.device.physical_circuit.qubits[
                    self.device.mp_2_dp_mapping[(module.index, module_physical_qubit)]
                ]
                for module_physical_qubit in range(module.size)
            ]
            print("Module {:d} --> device physical qubits {}".format(module.index,device_physical_qubits))
            print(module.physical_circuit)
            self.device.physical_circuit.compose(
                module.physical_circuit, qubits=device_physical_qubits, inplace=True
            )
        print("Combined into")
        print(self.device.physical_circuit)
        print("Depth {:d}. Size {:d}.".format(
            self.device.physical_circuit.depth(),
            self.device.physical_circuit.size()))