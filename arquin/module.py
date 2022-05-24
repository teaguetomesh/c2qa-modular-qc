import copy

import networkx as nx
import qiskit


class Module:
    """Class representing a single module within a distributed quantum computer.

    Provides properties ``graph``, ``qubits``, ``module_index``, ``size``, ``dag``, and ``mapping``.

    The nodes of the module graph represent individual qubits.
    m2d_p2v_mapping: module to device, physical to virtual mapping
    """

    def __init__(self, graph: nx.Graph, module_index: int) -> None:
        """
        The module graph represents the coupling map between contiguously labelled module qubits starting at
        index i=0. The module_index is used to map between module and device qubits.
        """
        self.graph = graph
        self.qubits = list(sorted(graph.nodes))
        self.module_index = module_index
        self.size = self.graph.size()
        module_circuit = qiskit.QuantumCircuit(self.graph.size())
        self.dag = qiskit.converters.circuit_to_dag(module_circuit)
        self.m2d_p2v_mapping = {}

    def add_device_virtual_qubit(self, qubit: qiskit.circuit.Qubit) -> None:
        self.m2d_p2v_mapping[len(self.m2d_p2v_mapping)] = qubit
        assert len(self.m2d_p2v_mapping) <= self.size

    def update_mapping(self, circuit: qiskit.QuantumCircuit) -> None:
        """
        Update the mapping based on the SWAPs in the circuit
        """
        # print(circuit)
        print("Mapping before compile :", self.mapping)
        # print(circuit._layout.get_physical_bits())
        new_initial_mapping = copy.deepcopy(self.mapping)
        for module_physical_qubit in circuit._layout.get_physical_bits():
            module_virtual_qubit = circuit._layout.get_physical_bits()[module_physical_qubit]
            print(module_physical_qubit, module_virtual_qubit)
            new_initial_mapping[module_physical_qubit] = self.mapping[
                circuit.qubits.index(module_virtual_qubit)
            ]
        self.mapping = new_initial_mapping
        print("Mapping after compile :", self.mapping)
        dag = qiskit.converters.circuit_to_dag(circuit)
        for gate in dag.topological_op_nodes():
            if gate.op.name == "swap":
                physical_qubits = [circuit.qubits.index(qarg) for qarg in gate.qargs]
                device_qubit_0, device_qubit_1 = [
                    self.mapping[physical_qubit] for physical_qubit in physical_qubits
                ]
                self.mapping[physical_qubits[0]] = device_qubit_1
                self.mapping[physical_qubits[1]] = device_qubit_0
        print("Final mapping after SWAPs :", self.mapping)
        print("-" * 10)
