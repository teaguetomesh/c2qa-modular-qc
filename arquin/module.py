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
        self.reset()

    def reset(self):
        self.virtual_circuit = qiskit.QuantumCircuit(self.graph.size())
        self.mv_2_dv_mapping = None
        self.mp_2_mv_mapping = None

    def add_virtual_gate(self, op, module_virtual_qargs) -> None:
        # print('{} Module {:d} {}'.format(op.name,self.module_index,module_virtual_qargs))
        self.virtual_circuit.append(op, qargs=module_virtual_qargs)

    def compile(self) -> None:
        coupling_map = arquin.converters.edges_to_coupling_map(self.graph.edges)
        self.physical_circuit = qiskit.compiler.transpile(
            self.virtual_circuit,
            coupling_map=coupling_map,
            initial_layout=self.mp_2_mv_mapping,
            layout_method="sabre",
            routing_method="sabre",
        )

    def update_mapping(self) -> None:
        """
        Update the mapping based on the SWAPs in the circuit
        """
        self.mp_2_mv_mapping = {}
        for module_physical_qubit in self.physical_circuit._layout.get_physical_bits():
            module_virtual_qubit = self.physical_circuit._layout.get_physical_bits()[
                module_physical_qubit
            ]
            self.mp_2_mv_mapping[module_physical_qubit] = module_virtual_qubit
        physical_dag = qiskit.converters.circuit_to_dag(self.physical_circuit)
        for gate in physical_dag.topological_op_nodes():
            if gate.op.name == "swap":
                module_physical_qargs = [
                    self.physical_circuit.qubits.index(qubit) for qubit in gate.qargs
                ]
                module_virtual_qubits = [
                    self.mp_2_mv_mapping[module_physical_qubit]
                    for module_physical_qubit in module_physical_qargs
                ]
                self.mp_2_mv_mapping[module_physical_qargs[0]] = module_virtual_qubits[1]
                self.mp_2_mv_mapping[module_physical_qargs[1]] = module_virtual_qubits[0]
