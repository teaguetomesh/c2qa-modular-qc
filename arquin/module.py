import copy

import networkx as nx
import qiskit


class Module:
    """Class representing a single module within a distributed quantum computer.

    Provides properties ``graph``, ``qubits``, ``module_index``, ``size``, ``dag``, and ``mapping``.

    The nodes of the module graph represent individual qubits.
    mp_2_dv_mapping: module to device, physical to virtual mapping
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
        self.mp_2_dv_mapping = {}
        self.dv_2_mp_mapping = {}
        self.mp_2_mv_mapping = {module_physical: self.dag.qubits[module_physical] for module_physical in range(self.dag.width())}

    def add_device_virtual_qubit(self, qubit: qiskit.circuit.Qubit) -> None:
        module_virtual_qubit = len(self.mp_2_dv_mapping)
        self.mp_2_dv_mapping[module_virtual_qubit] = qubit
        self.dv_2_mp_mapping[qubit] = module_virtual_qubit
        assert len(self.mp_2_dv_mapping) <= self.size
    
    def add_device_virtual_gate(self, gate, inactive_qubits) -> bool:
        module_qargs = []
        for device_virtual in gate.qargs:
            if device_virtual in self.dv_2_mp_mapping and device_virtual not in inactive_qubits:
                module_physical = self.dv_2_mp_mapping[device_virtual]
                module_virtual = self.mp_2_mv_mapping[module_physical]
                module_qargs.append(module_virtual)
        if len(module_qargs)==len(gate.qargs):
            print("Gate {:s} qargs {} --> Module {:d} qargs {}".format(gate.op.name,gate.qargs,self.module_index,module_qargs))
            self.dag.apply_operation_back(op=gate.op, qargs=module_qargs)
            return True
        else:
            return False

    def update_mapping(self, circuit: qiskit.QuantumCircuit) -> None:
        """
        Update the mapping based on the SWAPs in the circuit
        """
        print(circuit)
        print("mp_2_dv_mapping before compile :", self.mp_2_dv_mapping)
        new_mp_2_dv_mapping = copy.deepcopy(self.mp_2_dv_mapping)
        for module_physical_qubit in circuit._layout.get_physical_bits():
            module_virtual_qubit = circuit._layout.get_physical_bits()[module_physical_qubit]
            print(module_physical_qubit, module_virtual_qubit)

            # new_initial_mapping[module_physical_qubit] = self.mapping[
            #     circuit.qubits.index(module_virtual_qubit)
            # ]
        exit(1)
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
