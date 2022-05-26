from __future__ import annotations

import subprocess
from typing import Dict, List, Tuple

import numpy as np
import qiskit

import arquin


def construct_module_virtual_circuits(
    circuit: qiskit.QuantumCircuit, device: arquin.device.Device, distribution: np.ndarray
) -> Tuple[qiskit.QuantumCircuit, List]:
    """
    Construct the most number of gates for each module that can be scheduled without global comms
    1. Assign the qubits to each module based on front layer gates
    2. Assign as many gates as possible for each module
    """
    remaining_dag = qiskit.converters.circuit_to_dag(circuit)
    topological_op_nodes = list(remaining_dag.topological_op_nodes())
    inactive_qubits = set()
    for gate, module_idx in zip(topological_op_nodes, distribution):
        device_virtual_qargs = gate.qargs
        module_virtual_qargs = [device.dv_2_mv_mapping[device_virtual_qubit] for device_virtual_qubit in device_virtual_qargs]
        in_module = all([module_virtual_qubit[0]==module_idx for module_virtual_qubit in module_virtual_qargs])
        no_dependence = all([device_virtual_qubit not in inactive_qubits for device_virtual_qubit in device_virtual_qargs])
        if in_module and no_dependence:
            module = device.modules[module_idx]
            module_virtual_qargs = [module_virtual_qubit[1] for module_virtual_qubit in module_virtual_qargs]
            module.add_virtual_gate(gate.op, module_virtual_qargs)
            remaining_dag.remove_op_node(gate)
        else:
            """
            A qubit becomes inactive whenever any gate involving the qubit fails to add to its module
            """
            inactive_qubits.update(gate.qargs)
        if len(inactive_qubits) == remaining_dag.width():
            break

    remaining_circuit = qiskit.converters.dag_to_circuit(remaining_dag)
    return remaining_circuit