from qiskit.compiler import transpile
from time import perf_counter
import pickle
import networkx as nx

from qiskit_helper_functions.benchmarks import generate_circ

from device.main import Device
from compiler.converters import edges_to_coupling_map


def show_circuit_info(circuit):
    print(
        "Width = {:d}. Depth = {:d}. Number of nonlocal gates = {:d}. Ops = {}".format(
            circuit.width(), circuit.depth(), circuit.num_nonlocal_gates(), circuit.count_ops()
        ),
        flush=True,
    )


if __name__ == "__main__":
    ret = {}
    for num_modules in range(5, 51, 5):
        print("-" * 20, "%d Modules" % num_modules, "-" * 20, flush=True)
        ret[num_modules] = {}
        for module_size in range(10, 101, 10):
            device = Device(
                device_graph=nx.cycle_graph(num_modules),
                module_graphs=[nx.cycle_graph(module_size) for _ in range(num_modules)],
            )
            if device.size > 500:
                continue
            print("Module size = %d" % module_size, flush=True)
            circuit = generate_circ(
                num_qubits=device.size, depth=5, circuit_type="regular", reg_name="q", seed=None
            )
            show_circuit_info(circuit=circuit)
            compile_begin = perf_counter()
            coupling_map = edges_to_coupling_map(device.edges)
            transpiled_circuit = transpile(
                circuit, coupling_map=coupling_map, layout_method="sabre", routing_method="sabre"
            )
            compile_time = perf_counter() - compile_begin
            show_circuit_info(circuit=transpiled_circuit)
            print("compile_time = %.3e" % compile_time, flush=True)
            print()
            ret[num_modules][module_size] = {
                "device": device,
                "circuit": circuit,
                "transpiled_circuit": transpiled_circuit,
                "compile_time": compile_time,
            }
            pickle.dump(ret, open("experiments/profile_qiskit.pckl", "wb"))
        print("-" * 50, flush=True)
