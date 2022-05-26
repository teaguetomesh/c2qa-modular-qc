import subprocess
import numpy as np
import qiskit
from typing import Dict, List, Tuple
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

def assign_device_virtual_qubits(
    distribution: np.ndarray, circuit: qiskit.QuantumCircuit, device
) -> Dict:
    dag = qiskit.converters.circuit_to_dag(circuit)
    topological_op_nodes = list(dag.topological_op_nodes())
    dv_2_mv_mapping = {}
    module_virtual_qubit_counter = {module.module_index:0 for module in device.modules}
    for device_virtual_qubit in dag.qubits:
        gates_on_qubit = list(dag.nodes_on_wire(device_virtual_qubit, only_ops=True))
        if len(gates_on_qubit) > 0:
            first_gate = gates_on_qubit[0]
            gate_idx = topological_op_nodes.index(first_gate)
            module_idx = distribution[gate_idx]
            module = device.modules[module_idx]
            # TODO: need to fix for subsequent recursions
            module_virtual_qubit = module.virtual_circuit.qubits[module_virtual_qubit_counter[module_idx]]
            module_virtual_qubit_counter[module_idx] += 1
            dv_2_mv_mapping[device_virtual_qubit] = (module_idx, module_virtual_qubit)
    return dv_2_mv_mapping