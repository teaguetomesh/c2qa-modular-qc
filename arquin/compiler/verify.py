import copy, qiskit

def verify_physical_equivalence(circuit_a,circuit_b,circuit_b_initial_layout):
    '''
    Verify if circuit_a and circuit_b are physically equivalent
    By comparing the topological order of the gates.
    Does NOT consider if the logical gates can cancel.
    i.e. --X--X--H-- is not considered to be equivalent with --H--.

    circuit_b_initial_layout:
    the initial qubit layout of circuit_b
    [i] = j --> qubit i in circuit_b represents qubit j in circuit_a
    '''
    circuit_a = copy.deepcopy(circuit_a)
    circuit_b = copy.deepcopy(circuit_b)
    mapping = copy.deepcopy(circuit_b_initial_layout)
    
    dag_a = qiskit.converters.circuit_to_dag(circuit_a)
    dag_b = qiskit.converters.circuit_to_dag(circuit_b)
    for vertex_b in dag_b.topological_op_nodes():
        op_name_b = vertex_b.op.name
        if op_name_b=='swap':
            physical_swap_from = vertex_b.qargs[0].index
            physical_swap_to = vertex_b.qargs[1].index
            logical_swap_from = mapping[physical_swap_from]
            logical_swap_to = mapping[physical_swap_to]
            mapping[physical_swap_from] = logical_swap_to
            mapping[physical_swap_to] = logical_swap_from
        else:
            circuit_b_qubits = [x.index for x in vertex_b.qargs]
            circuit_a_qubits = []
            for circuit_b_qubit in circuit_b_qubits:
                circuit_a_qubit = mapping[circuit_b_qubit]
                circuit_a_qubits.append(circuit_a_qubit)
            # print('{:s} {} in circuit_b --> looking for {:s} {} in circuit_a'.format(
            #     op_name_b,circuit_b_qubits,op_name_b,circuit_a_qubits
            # ))
            circuit_a_qubits_visited = set()
            found_gate_in_circuit_a = False
            for vertex_a in dag_a.topological_op_nodes():
                op_name_a = vertex_a.op.name
                qubits = [qarg.index for qarg in vertex_a.qargs]
                vertex_on_frontier = all([qubit not in circuit_a_qubits_visited for qubit in qubits])
                [circuit_a_qubits_visited.add(qubit) for qubit in qubits]
                if vertex_on_frontier and qubits==circuit_a_qubits and op_name_a==op_name_b:
                    dag_a.remove_op_node(vertex_a)
                    found_gate_in_circuit_a = True
                    break
            assert found_gate_in_circuit_a
            dag_b.remove_op_node(vertex_b)
        circuit_a = qiskit.converters.dag_to_circuit(dag_a)
        circuit_b = qiskit.converters.dag_to_circuit(dag_b)
    return circuit_a.size()==0