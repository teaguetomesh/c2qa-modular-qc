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


def construct_local_circuits(
    circuit: qiskit.QuantumCircuit, device: arquin.device.Device, distribution: np.ndarray
) -> Tuple[qiskit.QuantumCircuit, List]:
    """
    Construct the most number of gates for each module that can be scheduled without global comms
    1. Assign the qubits to each module based on front layer gates
    2. Assign as many gates as possible for each module
    """
    remaining_dag = qiskit.converters.circuit_to_dag(circuit)
    
    local_dags = [
        qiskit.converters.circuit_to_dag(qiskit.QuantumCircuit(len(module.qubits)))
        for module in device.modules
    ]
    topological_op_nodes = list(remaining_dag.topological_op_nodes())
    inactive_qubits = set()
    for gate, module_idx in zip(topological_op_nodes, distribution):
        module = device.modules[module_idx]
        local_dag = local_dags[module_idx]
        module_qargs = []
        for qarg in gate.qargs:
            if qarg in module.d2m_v2p_mapping and qarg not in inactive_qubits:
                module_qubit = module.d2m_v2p_mapping[qarg]
                module_qarg = local_dag.qubits[module_qubit]
                module_qargs.append(module_qarg)
        if len(module_qargs) == len(gate.qargs):
            # print("Gate {:s} qargs {} --> Module {:d} {}".format(gate.op.name,gate.qargs,module_idx,module_qargs))
            local_dag.apply_operation_back(op=gate.op, qargs=module_qargs)
            remaining_dag.remove_op_node(gate)
        else:
            """
            A qubit becomes inactive whenever any gate involving the qubit fails to get assigned
            """
            inactive_qubits.update(gate.qargs)
            # print('inactive_qubits =',inactive_qubits)
        if len(inactive_qubits) == remaining_dag.width():
            break

    remaining_circuit = qiskit.converters.dag_to_circuit(remaining_dag)
    local_circuits = [qiskit.converters.dag_to_circuit(dag) for dag in local_dags]
    return remaining_circuit, local_circuits


def assign_qubits(
    distribution: np.ndarray, circuit: qiskit.QuantumCircuit, device: arquin.device.Device
) -> Dict:
    dag = qiskit.converters.circuit_to_dag(circuit)
    topological_op_nodes = list(dag.topological_op_nodes())
    module_qubit_assignments: Dict = {module_idx: [] for module_idx in range(len(device.modules))}
    for qubit in dag.qubits:
        gates_on_qubit = list(dag.nodes_on_wire(qubit, only_ops=True))
        if len(gates_on_qubit) > 0:
            first_gate = gates_on_qubit[0]
            gate_idx = topological_op_nodes.index(first_gate)
            module_idx = distribution[gate_idx]
            module_qubit_assignments[module_idx].append(qubit)
    all_qubits = []
    for module_idx in module_qubit_assignments:
        assert len(module_qubit_assignments[module_idx]) <= len(device.modules[module_idx].qubits)
        all_qubits += module_qubit_assignments[module_idx]
    for qubit in circuit.qubits:
        assert all_qubits.count(qubit) <= 1
    return module_qubit_assignments


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
