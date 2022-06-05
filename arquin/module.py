import copy
import networkx as nx
import qiskit

import arquin

class FrozenClass(object):
    __isfrozen = False
    def __setattr__(self, key, value):
        if self.__isfrozen and not hasattr(self, key):
            raise TypeError( "%r is a frozen class" % self )
        object.__setattr__(self, key, value)

    def _freeze(self):
        self.__isfrozen = True

class Module(FrozenClass):
    """Class representing a single module within a distributed quantum computer.

    Provides properties ``graph``, ``qubits``, ``module_index``, ``size``, ``dag``, and ``mapping``.

    The nodes of the module graph represent individual qubits.
    mp_2_dv_mapping: module to device, physical to virtual mapping
    """

    def __init__(self, graph: nx.Graph, index: int) -> None:
        """
        The module graph represents the coupling map between contiguously labelled module qubits starting at
        index i=0. The module_index is used to map between module and device qubits.
        """
        self.graph = graph
        self.index = index
        self.size = self.graph.size()
        self.coupling_map = arquin.converters.edges_to_coupling_map(self.graph.edges)
        self.mv_2_dv_mapping = None
        self.mp_2_mv_mapping = None
        self.virtual_circuit = None
        self.physical_circuit = None
        self._freeze()

    def compile(self) -> None:
        self.physical_circuit = qiskit.compiler.transpile(
            self.virtual_circuit,
            coupling_map=self.coupling_map,
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
