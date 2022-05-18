import subprocess
from qiskit import QuantumCircuit
import numpy as np
from qiskit.converters import circuit_to_dag, dag_to_circuit

def distribute_gates(source_fname, target_fname):
    subprocess.call(['/home/weit/scotch/build/bin/gmap',
    'workspace/%s_source.txt'%source_fname,
    'workspace/%s_target.txt'%target_fname,
    'workspace/%s_%s_distribution.txt'%(source_fname,target_fname)])

def construct_local_circuits(circuit, device, distribution):
    '''
    Construct the most number of gates for each module that can be scheduled without global comms
    1. Assign the qubits to each module based on front layer gates
    2. Assign as many gates as possible for each module
    '''
    dag = circuit_to_dag(circuit)
    local_dags, remaining_dag = assign_gates(distribution=distribution, dag=dag, device=device)
    remaining_circuit = dag_to_circuit(remaining_dag)
    local_circuits = [dag_to_circuit(dag)for dag in local_dags]
    return remaining_circuit, local_circuits

def assign_qubits(distribution, circuit, device):
    dag = circuit_to_dag(circuit)
    topological_op_nodes = list(dag.topological_op_nodes())
    module_qubit_assignments = {module_idx:[] for module_idx in range(len(device.modules))}
    for qubit in dag.qubits:
        gates_on_qubit = list(dag.nodes_on_wire(qubit,only_ops=True))
        if len(gates_on_qubit)>0:
            first_gate = gates_on_qubit[0]
            gate_idx = topological_op_nodes.index(first_gate)
            module_idx = distribution[gate_idx]
            module_qubit_assignments[module_idx].append(qubit)
    all_qubits = []
    for module_idx in module_qubit_assignments:
        assert len(module_qubit_assignments[module_idx])<=len(device.modules[module_idx].qubits)
        all_qubits += module_qubit_assignments[module_idx]
    for qubit in circuit.qubits:
        assert all_qubits.count(qubit)<=1
    return module_qubit_assignments

def assign_gates(distribution, dag, device):
    local_dags = [circuit_to_dag(QuantumCircuit(len(module.qubits))) for module in device.modules]
    topological_op_nodes = list(dag.topological_op_nodes())
    inactive_qubits = set()
    for gate, module_idx in zip(topological_op_nodes, distribution):
        module = device.modules[module_idx]
        local_dag = local_dags[module_idx]
        module_qargs = []
        for qarg in gate.qargs:
            if qarg in module.mapping and qarg not in inactive_qubits:
                module_qubit = module.mapping.index(qarg)
                module_qarg = local_dag.qubits[module_qubit]
                module_qargs.append(module_qarg)
        if len(module_qargs)==len(gate.qargs):
            # print(gate.op.name,gate.qargs,'--> module_%d'%module_idx,module_qargs)
            local_dag.apply_operation_back(op=gate.op,qargs=module_qargs)
            dag.remove_op_node(gate)
        else:
            '''
            A qubit becomes inactive whenever any gate involving the qubit fails to get assigned
            '''
            inactive_qubits.update(gate.qargs)
            # print('inactive_qubits =',inactive_qubits)
        if len(inactive_qubits)==dag.width():
            break
    return local_dags, dag

def read_distribution_file(distribution_fname):
    file = open('workspace/%s_distribution.txt'%distribution_fname,'r')
    lines = file.readlines()
    file.close()
    distribution = np.zeros(len(lines[1:]),dtype=int)
    for line in lines[1:]:
        line = line.strip().split('\t')
        gate_idx = int(line[0])
        module_idx = int(line[1])
        distribution[gate_idx] = module_idx
    return distribution