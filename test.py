import networkx as nx
import matplotlib.pyplot as plt
import qiskit

from qiskit_helper_functions.benchmarks import generate_circ

import arquin

if __name__ == "__main__":
    num_modules = 3
    module_size = 4
    # Last qubit of module i is connected to first qubit of module i+1
    global_edges = [[[i, module_size - 1], [(i + 1) % num_modules, 0]] for i in range(num_modules)]
    module_graph = nx.cycle_graph(module_size)
    device = arquin.Device(
        global_edges=global_edges, module_graphs=[module_graph for _ in range(num_modules)]
    )
    # for var in vars(device):
    #     print(var,vars(device)[var])

    circuit = generate_circ(
        num_qubits=device.size,
        depth=1,
        circuit_type="regular",
        reg_name="q",
        connected_only=False,
        seed=None,
    )

    coupling_map = arquin.converters.edges_to_coupling_map(device.physical_qubit_graph.edges)
    transpiled_circuit = qiskit.compiler.transpile(
        circuit, coupling_map=coupling_map, layout_method="sabre", routing_method="sabre"
    )
    print(f"Qiskit depth {circuit.depth()} --> {transpiled_circuit.depth()}")

    compiler = arquin.ModularCompiler(
        circuit=circuit, circuit_name="regular", device=device, device_name="ring"
    )
    compiler.run()

    # nx.draw(device_graph)
    # plt.savefig('workspace/device.pdf')
    # plt.close()

    # nx.draw(module_graph)
    # plt.savefig('workspace/module.pdf')
    # plt.close()

    # detailed_device = nx.Graph()
    # detailed_device.add_edges_from(device.edges)
    # nx.draw(detailed_device,with_labels=True)
    # plt.savefig('workspace/detailed_device.pdf')
    # plt.close()
