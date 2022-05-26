from __future__ import annotations

import subprocess
from typing import Dict, List, Tuple

import numpy as np
import qiskit

import arquin


def distribute_gates(source_fname: str, target_fname: str) -> None:
    subprocess.call(
        [
            "/home/weit/scotch/build/bin/gmap",
            "workspace/%s_source.txt" % source_fname,
            "workspace/%s_target.txt" % target_fname,
            "workspace/%s_%s_distribution.txt" % (source_fname, target_fname),
        ]
    )


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


def assign_device_virtual_qubits(
    distribution: np.ndarray, circuit: qiskit.QuantumCircuit, device: arquin.device.Device
) -> Dict:
    dag = qiskit.converters.circuit_to_dag(circuit)
    topological_op_nodes = list(dag.topological_op_nodes())
    for device_virtual_qubit in dag.qubits:
        gates_on_qubit = list(dag.nodes_on_wire(device_virtual_qubit, only_ops=True))
        if len(gates_on_qubit) > 0:
            first_gate = gates_on_qubit[0]
            gate_idx = topological_op_nodes.index(first_gate)
            module_idx = distribution[gate_idx]
            module = device.modules[module_idx]
            module_virtual_qubit = module.virtual_circuit.qubits[len(module.mv_2_dv_mapping)]
            module.mv_2_dv_mapping[module_virtual_qubit] = device_virtual_qubit
            device.dv_2_mv_mapping[device_virtual_qubit] = (module_idx, module_virtual_qubit)
    check_qubit_assignment_valid(circuit, device)


def check_qubit_assignment_valid(circuit, device):
    all_qubits = []
    for module in device.modules:
        assert len(module.mv_2_dv_mapping) <= module.size
        all_qubits += list(module.mv_2_dv_mapping.values())
    for qubit in circuit.qubits:
        assert all_qubits.count(qubit) <= 1


def read_distribution_file(distribution_fname: str) -> np.ndarray:
    file = open("workspace/%s_distribution.txt" % distribution_fname, "r")
    lines = file.readlines()
    file.close()
    distribution = np.zeros(len(lines[1:]), dtype=int)
    for line in lines[1:]:
        split_line = line.strip().split("\t")
        gate_idx = int(split_line[0])
        module_idx = int(split_line[1])
        distribution[gate_idx] = module_idx
    return distribution
