import networkx as nx
import matplotlib.pyplot as plt
from qiskit.compiler import transpile
from qiskit.transpiler import CouplingMap

from qiskit_helper_functions.benchmarks import generate_circ

from arquin.device.main import Device
from arquin.compiler.main import ModularCompiler
from arquin.compiler.converters import edges_to_coupling_map

if __name__ == '__main__':
    num_modules = 3
    module_size = 4
    device_graph = nx.cycle_graph(num_modules)
    module_graph = nx.cycle_graph(module_size)
    device = Device(
        device_graph=device_graph,
        module_graphs=[module_graph for _ in range(num_modules)])

    circuit = generate_circ(num_qubits=device.size,depth=1,circuit_type='regular',reg_name='q',connected_only=False,seed=None)

    coupling_map = edges_to_coupling_map(device.global_edges+device.local_edges)
    transpiled_circuit = transpile(circuit,coupling_map=coupling_map,layout_method='sabre',routing_method='sabre')
    print('Qiskit depth %d --> %d'%(circuit.depth(), transpiled_circuit.depth()))

    compiler = ModularCompiler(circuit=circuit,circuit_name='regular',device=device,device_name='ring')
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
