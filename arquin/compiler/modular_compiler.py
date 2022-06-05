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

        remaining_virtual_circuit = copy.deepcopy(self.virtual_circuit)
        recursion_counter = 0
        while remaining_virtual_circuit.size() > 0:
            print("*" * 20, "Recursion %d" % recursion_counter, "*" * 20)
            print("remaining_virtual_circuit size %d" % remaining_virtual_circuit.size())

            for module in self.device.modules:
                module.reset_virtual_circuit()

            print("Step 1: Distribute the virtual gates in remaining_virtual_circuit to modules")
            vertex_weights, edges = arquin.converters.circuit_to_graph(
                circuit=remaining_virtual_circuit
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
                distribution=gate_distribution,
                circuit=remaining_virtual_circuit,
                device=self.device,
            )
            for module_index in qubit_distribution:
                print("Module {:d} : {}".format(module_index, qubit_distribution[module_index]))
            print("-" * 10)

            print("Step 3: Insert global communication")
            self.global_comm(qubit_distribution)
            print("-" * 10)
            exit(1)

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
        if self.device.dp_2_dv_mapping is None:
            print("First iteration does not need global communications")
            for module in self.device.modules:
                module.mv_2_dv_mapping = {}
                for qubit_counter in range(len(qubit_distribution[module.index])):
                    device_virtual_qubit = qubit_distribution[module.index][qubit_counter]
                    module_virtual_qubit = module.virtual_circuit.qubits[qubit_counter]
                    module.mv_2_dv_mapping[module_virtual_qubit] = device_virtual_qubit
        else:
            print("Need global routing")
            exit(1)
        for module in self.device.modules:
            print("Module {:d} mv_2_dv_mapping :".format(module.index))
            for module_virtual_qubit in module.mv_2_dv_mapping:
                print(
                    "{} --> {}".format(
                        module_virtual_qubit, module.mv_2_dv_mapping[module_virtual_qubit]
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
