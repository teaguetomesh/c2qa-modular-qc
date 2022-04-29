from qiskit.compiler import transpile
from time import perf_counter
import pickle

from qiskit_helper_functions.benchmarks import generate_circ

from device.ring import Ring

def show_circuit_info(circuit):
    print('Width = {:d}. Depth = {:d}. Number of nonlocal gates = {:d}. Ops = {}'.format(
        circuit.width(),circuit.depth(),circuit.num_nonlocal_gates(),circuit.count_ops()
    ),flush=True)

if __name__ == '__main__':
    ret = {}
    for num_modules in range(5,51,5):
        print('-'*20,'%d Modules'%num_modules,'-'*20,flush=True)
        ret[num_modules] = {}
        for module_size in range(10,101,10):
            print('Module size = %d'%module_size,flush=True)
            device = Ring(num_modules=num_modules,module_size=module_size)
            circuit = generate_circ(num_qubits=len(device.qubits),depth=5,circuit_type='regular',reg_name='q',seed=None)
            show_circuit_info(circuit=circuit)
            compile_begin = perf_counter()
            transpiled_circuit = transpile(circuit,coupling_map=device.edges,layout_method='sabre',routing_method='sabre')
            compile_time = perf_counter()-compile_begin
            show_circuit_info(circuit=transpiled_circuit)
            print('compile_time = %.3e'%compile_time,flush=True)
            print()
            ret[num_modules][module_size] = {
                'device':device,
                'circuit':circuit,
                'transpiled_circuit':transpiled_circuit,
                'compile_time':compile_time
                }
            pickle.dump(ret,open('qiskit.pckl','wb'))
        print('-'*50,flush=True)