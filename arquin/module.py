import copy

import networkx as nx
import qiskit

import arquin


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
        self.module_index = module_index
        self.size = self.graph.size()
        self.virtual_circuit = qiskit.QuantumCircuit(self.graph.size())
        self.mv_2_dv_mapping = {}

    def add_virtual_gate(self, op, module_virtual_qargs) -> None:
        # print('{} Module {:d} {}'.format(op.name,self.module_index,module_virtual_qargs))
        self.virtual_circuit.append(op,qargs=module_virtual_qargs)

    def compile(self, has_initial_layout) -> None:
        # print(self.circuit)
        # print("mp_2_mv_mapping before SWAPs :", self.mp_2_mv_mapping)
        if has_initial_layout:
            initial_layout = self.mp_2_mv_mapping
        else:
            initial_layout = None
        coupling_map = arquin.converters.edges_to_coupling_map(self.graph.edges)
        self.circuit = qiskit.compiler.transpile(
            self.circuit,
            coupling_map=coupling_map,
            initial_layout=initial_layout,
            routing_method="sabre",
        )

    def update_mapping(self) -> None:
        """
        Update the mapping based on the SWAPs in the circuit
        """
        dag = qiskit.converters.circuit_to_dag(self.circuit)
        for gate in dag.topological_op_nodes():
            if gate.op.name == "swap":
                module_physical_qargs = [self.circuit.qubits.index(qubit) for qubit in gate.qargs]
                module_virtual_qubits = [self.mp_2_mv_mapping[module_physical_qubit] for module_physical_qubit in module_physical_qargs]
                self.mp_2_mv_mapping[module_physical_qargs[0]] = module_virtual_qubits[1]
                self.mp_2_mv_mapping[module_physical_qargs[1]] = module_virtual_qubits[0]
        # print(self.circuit)
        # print("mp_2_mv_mapping after SWAPs :", self.mp_2_mv_mapping)