from qiskit.compiler import transpile

from qiskit_helper_functions.benchmarks import generate_circ

from device.ring import Ring

device = Ring(num_modules=10,module_size=10)

circuit = generate_circ(num_qubits=len(device.qubits),depth=5,circuit_type='supremacy',reg_name='q',seed=None)
print(circuit.width(),circuit.depth(),circuit.num_nonlocal_gates())

transpiled_circuit = transpile(circuit,coupling_map=device.edges,layout_method='sabre',routing_method='sabre')
print(transpiled_circuit.width(),transpiled_circuit.depth(),transpiled_circuit.num_nonlocal_gates())