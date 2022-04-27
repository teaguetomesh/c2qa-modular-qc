from qiskit_helper_functions.benchmarks import generate_circ
from qiskit_helper_functions.non_ibmq_functions import circuit_stripping

from device.ring import Ring
from compiler.converters import edges_to_source_graph, circuit_to_edges, write_source_graph_file, write_target_graph_file
from compiler.distribute import distribute

if __name__ == '__main__':
    device = Ring(num_modules=5,module_size=10)
    device_graph = edges_to_source_graph(n_vertices=len(device.qubits),edges=device.edges)
    write_source_graph_file(graph=device_graph, fname='device')
    write_target_graph_file(fname='device')

    circuit = generate_circ(num_qubits=len(device.qubits),depth=5,circuit_type='regular',reg_name='q',seed=None)
    stripped_circuit = circuit_stripping(circuit=circuit)
    n_vertices, edges, _, _ = circuit_to_edges(circuit=stripped_circuit)
    circuit_graph = edges_to_source_graph(n_vertices=n_vertices,edges=edges)
    write_source_graph_file(graph=circuit_graph, fname='circuit')

    distribute(source_fname='circuit',target_fname='device')